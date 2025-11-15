"""Connection utilities for multiple data stores.

This module provides lightweight wrapper classes for connecting to and
interacting with common services used in tests: MySQL, Redis, ClickHouse,
MongoDB, and SSH. Each wrapper handles simple operations and ensures
resources are closed where appropriate.
"""

import sys
import traceback
import pymongo
import pandas as pd
import pymysql
import redis
from clickhouse_sqlalchemy import make_session
from sqlalchemy import create_engine
from conf.operator_config import OperatorConfig
from common.record_log import logs
import paramiko

conf = OperatorConfig()

class MysqlConnection:
    """Simple MySQL connection wrapper.

    Connects using configuration from `conf` and exposes helper methods
    to execute queries and close the connection.
    """
    def __init__(self):
        """Open a MySQL connection and create a dict cursor.

        Reads connection parameters from configuration and attempts to
        establish a connection. On failure `self.connection` is set to None.
        """
        mysql_conf = {
            'host': conf.get_section_mysql('host'),
            'port': int(conf.get_section_mysql('port')),
            'user': conf.get_section_mysql('username'),
            'password': conf.get_section_mysql('password'),
            'database': conf.get_section_mysql('database')
        }

        try:
            # Create connection and a dict cursor for easy column access
            self.connection = pymysql.connect(
                **mysql_conf,
                charset='utf8'
            )
            self.cursor = self.connection.cursor(cursor=pymysql.cursors.DictCursor)
            logs.info(f"Connected to MySQL database {mysql_conf['database']} successfully.")
        except Exception as e:
            logs.error(f"Failed to connect to MySQL database: {e}")
            self.connection = None

    def close(self):
        """Close cursor and connection if open."""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            logs.info("MySQL connection closed.")

    def execute_query(self, query):
        """Execute a SELECT query and return the first row as a list-of-values.

        The original code collects rows, converts each row dict to a list of
        values and returns the first formatted row wrapped in a list. If no
        connection or an error occurs, returns None.
        """
        try:
            if self.connection is None:
                logs.error("No MySQL connection available.")
                return None
            # Execute the provided query and commit any transactional changes
            self.cursor.execute(query)
            self.connection.commit()
            res = self.cursor.fetchall()

            values = []

            for ite in res:
                # Convert each row (dict) to a list of values preserving column order
                values.append(list(ite.values()))

            for val in values:
                lst_format = [
                    val
                ]
                # Return only the first formatted row as in original implementation
                return lst_format
        except Exception as e:
            logs.error(f"Error executing MySQL query: {e}")
            return None
        finally:
            # Ensure resources are closed regardless of outcome
            self.close()

    def delete_query(self, query):
        """Execute a DELETE (or other write) SQL statement and commit.

        Closes the connection after execution. Returns None but logs errors.
        """
        try:
            if self.connection is None:
                logs.error("No MySQL connection available.")
                return None
            # Execute and commit a modifying query
            self.cursor.execute(query)
            self.connection.commit()
            logs.info("Delete query executed successfully.")
        except Exception as e:
            logs.error(f"Error executing delete query: {e}")
        finally:
            self.close()


class RedisConnection:
    """Redis connection helper.

    Wraps a Redis client created from configuration and exposes common
    operations like set/get and hash helpers.
    """
    def __init__(self, ip=conf.get_section_redis("host"), port=conf.get_section_redis("port"), username=None,
                 passwd=None, db=conf.get_section_redis("db")):
        """Create a connection pool and Redis client instance.

        decode_responses=True is used so operations return strings instead
        of bytes.
        """
        self.host = ip
        self.port = port
        self.username = username
        self.password = passwd
        self.db = db

        try:
            pool = redis.ConnectionPool(
                host=self.host,
                port=int(self.port),
                password=self.password
            )
            # Client using the connection pool
            self.first_conn = redis.Redis(connection_pool=pool,decode_responses=True)
        except Exception:
            logs.error(str(traceback.format_exc()))

    def set_kv(self,key,value,expire=None):
        """Set a key with optional expiration (seconds).

        Uses setex if an expire time is provided, otherwise set().
        """
        try:
            if expire:
                self.first_conn.setex(key,expire,value)
            else:
                self.first_conn.set(key,value)
            logs.info(f"Set key '{key}' with value '{value}' in Redis.")
        except Exception as e:
            logs.error(f"Error setting key in Redis: {e}")

    def get_kv(self,key):
        """Get the value of a key. Returns None if error occurs."""
        try:
            value = self.first_conn.get(key)
            logs.info(f"Retrieved key '{key}' with value '{value}' from Redis.")
            return value
        except Exception as e:
            logs.error(f"Error getting key from Redis: {e}")
            return None

    def hash_set(self, key, value, ex=None):
        """Set a key with optional expiry; kept simple to mirror original behavior."""
        try:
            return self.first_conn.set(name=key, value=value, ex=ex)
        except Exception:
            logs.error(str(traceback.format_exc()))

    def hash_hget(self, names, keys):
        """Get a field from a hash (hget)."""
        try:
            data = self.first_conn.hget(names, keys)
            return data
        except Exception:
            logs.error(str(traceback.format_exc()))

    def hash_hmget(self, name, keys, *args):
        """Get multiple fields from a hash (hmget).

        Validates that `keys` is a list before calling hmget.
        """
        if not isinstance(keys, list):
            logs.error("Keys must be provided as a list.")
            return None
        try:
            return self.first_conn.hmget(name, keys, *args)
        except Exception:
            logs.error(str(traceback.format_exc()))

class ClickHouseConnection:
    """ClickHouse connection wrapper using SQLAlchemy engine and session."""
    def __init__(self):

        config = {
            'server_host': conf.get_section_clickhouse('host'),
            'port': conf.get_section_clickhouse('port'),
            'user': conf.get_section_clickhouse('username'),
            'password': conf.get_section_clickhouse('password'),
            'db': conf.get_section_clickhouse('db'),
            'send_receive_timeout': conf.get_section_clickhouse('timeout')
        }
        try:
            # Build ClickHouse connection URL and create an engine
            connection = 'clickhouse://{user}:{password}@{server_host}:{port}/{db}'.format(**config)
            engine = create_engine(connection, pool_size=100, pool_recycle=3600, pool_timeout=20)
            self.session = make_session(engine)
        except Exception as e:
            logs.error(f"Failed to connect to ClickHouse database: {e}")

    def execute_query(self, query):
        """Execute a query and return results as a pandas DataFrame."""
        cursor = self.session.execute(query)
        try:
            fields = cursor.keys()
            # Map rows to dicts and construct DataFrame
            df = pd.DataFrame([dict(zip(fields, item)) for item in cursor.fetchall()])
            return df
        except:
            logs.error(str(traceback.format_exc()))
        finally:
            # Ensure cursor and session are closed
            cursor.close()
            self.session.close()


class MongoConnection:
    """MongoDB helper class wrapping pymongo operations for convenience."""

    def __init__(self):

        mg_conf = {
            'host': conf.get_section_mongodb("host"),
            'port': int(conf.get_section_mongodb("port")),
            'user': conf.get_section_mongodb("username"),
            'passwd': conf.get_section_mongodb("password"),
            'db': conf.get_section_mongodb("database")
        }

        try:
            # Create a MongoClient and select the configured database
            client = pymongo.MongoClient(
                'mongodb://{user}:{passwd}@{host}:{port}/{db}'.format(**mg_conf))
            self.db = client[mg_conf['db']]
            logs.info("Connected to MongoDB database successfully.")
        except Exception as e:
            logs.error(e)

    def use_collection(self, collection):
        """Return a collection object by name."""
        try:
            collect_table = self.db[collection]
        except Exception as e:
            logs.error(e)
        else:
            return collect_table

    def insert_one_data(self, data, collection):
        """Insert a single document into the given collection."""
        try:
            self.use_collection(collection).insert_one(data)
        except Exception as e:
            logs.error(e)

    def insert_many_data(self, documents, collection):
        """Insert multiple documents; expects a list of dicts."""
        if not isinstance(documents, list):
            raise TypeError("parameters must be of list type")
        try:
            self.use_collection(collection).insert_many(documents)
        except Exception as e:
            logs.error(e)

    def query_one_data(self, query_param, collection):
        """Find and return a single document matching `query_param`."""
        if not isinstance(query_param, dict):
            raise TypeError("query parameters must be of dict type")
        try:
            res = self.use_collection(collection=collection).find_one(query_param)
            return res
        except Exception as e:
            logs.error(e)

    def query_all_data(self, collection, query_param=None, limit_num=sys.maxsize):
        """Query multiple documents and return them as a list.

        If `query_param` is provided it must be a dict. `limit_num` limits
        the number of documents returned.
        """
        table = self.use_collection(collection)
        if query_param is not None:
            if not isinstance(query_param, dict):
                raise TypeError("query parameters must be of dict type")
        try:
            # Execute the query and convert the cursor to a list
            query_results = table.find(query_param).limit(limit_num)  # limit限制结果集查询数量
            res_list = [res for res in query_results]
            return res_list
        except Exception:
            logs.error(str(traceback.format_exc()))
            return None

    def update_collection(self, query_conditions, after_change, collection):
        """Update a single document that matches `query_conditions`.

        Performs a type check on inputs and only attempts update if a
        matching document exists.
        """
        if not isinstance(query_conditions, dict) or not isinstance(after_change, dict):
            raise TypeError("query_conditions and after_change must be of dict type")
        res = self.query_one_data(query_conditions, collection)
        if res is not None:
            try:
                # Use $set to update fields on the matched document
                self.use_collection(collection).update_one(query_conditions, {"$set": after_change})
            except Exception as e:
                logs.error(e)
                return None
        else:
            logs.info("No matching data found to update.")
            return None

    def delete_collection(self, search, collection):
        """Delete a single document matching `search`."""
        if not isinstance(search, dict):
            raise TypeError("parameters must be of dict type")
        try:
            self.use_collection(collection).delete_one(search)
        except Exception as e:
            logs.error(e)

    def delete_many_collection(self, search, collection):
        """Delete multiple documents matching `search`."""
        try:
            self.use_collection(collection).delete_many(search)
        except Exception:
            return None

    def drop_collection(self, collection):
        """Drop (delete) the named collection from the database."""
        try:
            self.use_collection(collection).drop()
            logs.info("delete success")
        except Exception:
            return None

class SSHConnection:
    """Simple SSH helper using paramiko to execute remote commands."""
    def __init__(self):
        """Create an SSH client and connect using configuration."""
        self.__conn_info = {
            'hostname': conf.get_section_ssh('host'),
            'port': int(conf.get_section_ssh('port')),
            'username': conf.get_section_ssh('username'),
            'password': conf.get_section_ssh('password'),
            'timeout': int(conf.get_section_ssh('timeout')),
        }

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Establish SSH connection; will raise on failure
        self.__client.connect(**self.__conn_info)

        if self.__client:
            logs.info("Connected to SSH successfully.")

    def get_ssh_content(self, command=None):
        """Execute `command` on the remote host and return stdout as text.

        If `command` is None the default command from configuration is used.
        """
        stdin, stdout, stderr = self.__client.exec_command(
            command if command is not None else conf.get_section_ssh('command'))
        content = stdout.read().decode()
        return content
