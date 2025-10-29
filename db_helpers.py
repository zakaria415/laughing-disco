import psycopg2
import pandas as pd
import streamlit as st # Assuming streamlit is available for error messages in the app context

def get_db_connection(db_url):
    """Establishes a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"⚠️ Database Connection Error: {e}")
        return None
    except Exception as e:
        st.error(f"⚠️ An unexpected error occurred while connecting to the database: {e}")
        return None


def create_analysis_table(db_url):
    """Creates the analysis_results table if it doesn't exist."""
    conn = get_db_connection(db_url)
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    url VARCHAR(2048),
                    sentiment_score FLOAT,
                    text_content TEXT,
                    analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            cur.close()
            # st.success("✅ Database table 'analysis_results' checked/created successfully.")
        except psycopg2.Error as e:
            st.error(f"⚠️ Database Error creating table: {e}")
            conn.rollback()
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred during table creation: {e}")
        finally:
            if conn is not None:
                conn.close()

def save_analysis_result(db_url, url, sentiment_score, text_content):
    """Saves a single analysis result to the database."""
    conn = get_db_connection(db_url)
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO analysis_results (url, sentiment_score, text_content)
                VALUES (%s, %s, %s);
            """, (url, sentiment_score, text_content))
            conn.commit()
            cur.close()
        except psycopg2.Error as e:
            st.error(f"⚠️ Database Error saving analysis result: {e}")
            conn.rollback()
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred while saving analysis result: {e}")
        finally:
            if conn is not None:
                conn.close()

def get_recent_analysis_data(db_url, limit=10):
    """Retrieves recent analysis data from the database."""
    conn = get_db_connection(db_url)
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT url, sentiment_score, analysis_time
                FROM analysis_results
                ORDER BY analysis_time DESC
                LIMIT %s;
            """, (limit,))
            data = cur.fetchall()
            columns = ['url', 'sentiment_score', 'analysis_time']
            df = pd.DataFrame(data, columns=columns)
            cur.close()
            return df
        except psycopg2.Error as e:
            st.error(f"⚠️ Database Error retrieving data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred while retrieving data: {e}")
            return pd.DataFrame() # Return empty DataFrame on error
        finally:
            if conn is not None:
                conn.close()
    return pd.DataFrame() # Return empty DataFrame if connection failed

