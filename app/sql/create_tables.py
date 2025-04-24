import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
def save_sessin_info_to_database(session_id, user_id, username):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO user_sessions (session_id, user_id, username)
            VALUES (%s, %s, %s)
        """)

        cursor.execute(insert_query,(
            session_id,
            user_id,
            username
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Session_info saved successfully!")

    except Exception as e:
        print(f"Error saving Session_info to database: {e}")

def save_generated_answer_to_database(session_id, user_question, user_description, artwork, generated_answer, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO generated_answers (session_id, user_question, user_description, artwork, generated_answer, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (
            session_id,
            user_question,
            user_description,
            artwork,
            generated_answer,
            voice_filename,
            generation_time_text_sec,
            generation_time_audio_sec
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Generated generated_answers saved successfully!")

    except Exception as e:
        print(f"Error saving generated_answers to database: {e}")

def save_generated_artwork_info_to_database(session_id, user_description, artwork, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO generated_artwork_info (session_id, user_description, artwork, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (
            session_id,
            user_description,
            artwork,
            generated_text,
            voice_filename,
            generation_time_text_sec,
            generation_time_audio_sec
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Generated artwork_info saved successfully!")

    except Exception as e:
        print(f"Error saving artwork_info to database: {e}")

def save_generated_goodbye_to_database(session_id, user_description, generated_goodbye_word, generation_time_text_sec):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO generated_goodbye (session_id, user_description, generated_goodbye_word, generation_time_text_sec)
            VALUES (%s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (
            session_id,
            user_description,
            generated_goodbye_word,
            generation_time_text_sec
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Generated generated_goodbye saved successfully!")

    except Exception as e:
        print(f"Error saving generated_goodbye to database: {e}")


def save_generated_route_to_database(session_id, user_description, user_query, k, artworks, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO generated_routes (session_id, user_description, user_query, k, artworks, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """)

        cursor.execute(insert_query, (
            session_id,
            user_description,
            user_query,
            k,
            artworks,
            generated_text,
            voice_filename,
            generation_time_text_sec,
            generation_time_audio_sec
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Generated route saved successfully!")

    except Exception as e:
        print(f"Error saving generated route to database: {e}")

def save_to_database(session_id, context, question, answer, result):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = ("""
            INSERT INTO hallucination_evaluations (session_id, context, question, answer, result)
            VALUES (%s, %s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (session_id, context, question, answer, result))

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully!")

    except Exception as e:
        print(f"Error saving to database: {e}")