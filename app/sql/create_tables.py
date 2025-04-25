import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    print("DB pool initialized")

async def close_db_pool():
    await pool.close()
    print("DB pool closed")

async def save_session_info_to_database(session_id, user_id, username):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_sessions (session_id, user_id, username)
                VALUES ($1, $2, $3)
            """, session_id, user_id, username)
        print("Session_info saved successfully!")
    except Exception as e:
        print(f"Error saving session_info: {e}")

async def save_generated_answer_to_database(session_id, user_question, user_description, artwork, generated_answer, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO generated_answers (session_id, user_question, user_description, artwork, generated_answer, voice_filename, generation_time_text_sec, generation_time_audio_sec)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, session_id, user_question, user_description, artwork, generated_answer, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            await conn.close()
        print("Generated answers saved successfully!")
    except Exception as e:
        print(f"Error saving generated_answers to database: {e}")

async def save_generated_artwork_info_to_database(session_id, user_description, artwork, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO generated_artwork_info (session_id, user_description, artwork, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, session_id, user_description, artwork, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            await conn.close()
        print("Generated artwork_info saved successfully!")
    except Exception as e:
        print(f"Error saving artwork_info to database: {e}")

async def save_generated_goodbye_to_database(session_id, user_description, generated_goodbye_word, generation_time_text_sec):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO generated_goodbye (session_id, user_description, generated_goodbye_word, generation_time_text_sec)
                VALUES ($1, $2, $3, $4)
            """, session_id, user_description, generated_goodbye_word, generation_time_text_sec)
            await conn.close()
        print("Generated goodbye saved successfully!")
    except Exception as e:
        print(f"Error saving generated_goodbye to database: {e}")

async def save_generated_route_to_database(session_id, user_description, user_query, k, artworks, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO generated_routes (session_id, user_description, user_query, k, artworks, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, session_id, user_description, user_query, k, artworks, generated_text, voice_filename, generation_time_text_sec, generation_time_audio_sec)
            await conn.close()
        print("Generated route saved successfully!")
    except Exception as e:
        print(f"Error saving generated route to database: {e}")

async def save_to_database(session_id, context, question, answer, result):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO hallucination_evaluations (session_id, context, question, answer, result)
                VALUES ($1, $2, $3, $4, $5)
            """, session_id, context, question, answer, result)
            await conn.close()
        print("Data saved successfully!")
    except Exception as e:
        print(f"Error saving to database: {e}")
