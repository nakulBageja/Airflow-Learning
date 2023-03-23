# User data extraction using Airflow
<img href='./assets/users_dag.png'>

## Providers used
1. PostgresOperator - Used to create a table
2. HttpSensor - Used to check if an API is available
3. SimpleHttpOperator - Used to send GET request to the API

## Operators used
1. PythonOperator - Used for executing custom python function

## Hooks used
1. PostgresHook - Used for saving extracted data to Postgres table

## Connection created
1. Postgres
2. Http
