CREATE TABLE IF NOT EXISTS cardio_programs (
  id SERIAL PRIMARY KEY,
  client_user_id INT NOT NULL,
  coach_user_id INT NOT NULL,
  title VARCHAR(255) DEFAULT 'Kardiyo Programı',
  is_active BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cardio_sessions (
  id SERIAL PRIMARY KEY,
  cardio_program_id INT NOT NULL REFERENCES cardio_programs(id) ON DELETE CASCADE,
  day_of_week VARCHAR(10) NOT NULL,
  cardio_type VARCHAR(50) NOT NULL,
  duration_min INT NOT NULL DEFAULT 30,
  notes TEXT,
  order_index INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
