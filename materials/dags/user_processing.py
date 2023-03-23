from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from datetime import datetime
from pandas import json_normalize
import json

# Python function to process the data


def _process_user(ti):
    # Getting the data from the extract_user dag
    users = ti.xcom_pull(task_ids='extract_user')
    user = users['results'][0]
    processed_user = json_normalize({
        'first_name': user['name']['first'],
        'last_name': user['name']['last'],
        'country': user['location']['country'],
        'username': user['login']['username'],
        'password': user['login']['password'],
        'email': user['email']
    })
    processed_user.to_csv('/tmp/processed_user.csv', index=None, header=False)

# Python function to store the user from CSV to table


def _store_users():
    hook = PostgresHook(postgres_conn_id='postgres')
    hook.copy_expert(
        sql="COPY users FROM stdin WITH DELIMITER as ','",
        filename='/tmp/processed_user.csv'
    )


with DAG('user_processing', start_date=datetime(2022, 1, 1), schedule_interval='@daily', catchup=False) as dag:
    # Task to create a table in postgres
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="""
            CREATE TABLE IF NOT EXISTS users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """
    )
    # Task to check whether an API is available or not, using Sensor operator
    is_api_available = HttpSensor(
        task_id='is_api_available',
        http_conn_id='user_api',
        endpoint='api/'
    )
    # Task to extract the data from the API
    extract_user = SimpleHttpOperator(
        task_id='extract_user',
        http_conn_id='user_api',
        endpoint='api/',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )
    # Task to process the extracted data using python
    process_user = PythonOperator(
        task_id='process_user',
        python_callable=_process_user
    )
    # Task to store user in POSTGRES table
    store_user = PythonOperator(
        task_id='store_user',
        python_callable=_store_users
    )

    # Setting up dependencies
    create_table >> is_api_available >> extract_user >> process_user >> store_user
