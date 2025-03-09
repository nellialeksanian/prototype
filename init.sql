CREATE TABLE hallucination_evaluations (
        id SERIAL PRIMARY KEY,
        context TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        result BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);