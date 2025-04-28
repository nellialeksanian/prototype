CREATE TABLE user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hallucination_evaluations (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    context TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE generated_routes (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_description TEXT,
    user_query TEXT,
    k INT NOT NULL,
    artworks TEXT[] NOT NULL,
    generated_text TEXT,
    generation_time_text_sec INT NOT NULL,
    generation_time_audio_sec INT,
    voice_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE generated_artwork_info (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    artwork TEXT NOT NULL,
    user_description TEXT,          
    generated_text TEXT,   
    voice_filename TEXT,
    generation_time_text_sec INT NOT NULL,
    generation_time_audio_sec INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE generated_answers (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    artwork TEXT NOT NULL,
    user_question TEXT NOT NULL,
    user_description TEXT,          
    generated_answer TEXT,
    voice_filename TEXT,
    generation_time_text_sec INT NOT NULL,
    generation_time_audio_sec INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
);
CREATE TABLE generated_goodbye (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_description TEXT,          
    generated_goodbye_word TEXT,
    generation_time_text_sec INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE CASCADE
)
