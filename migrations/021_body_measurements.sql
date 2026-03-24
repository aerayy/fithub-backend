-- Body measurements tracking table
CREATE TABLE IF NOT EXISTS body_measurements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measured_at DATE NOT NULL DEFAULT CURRENT_DATE,
    weight_kg DECIMAL(5,2),
    chest_cm DECIMAL(5,1),
    waist_cm DECIMAL(5,1),
    hips_cm DECIMAL(5,1),
    left_arm_cm DECIMAL(5,1),
    right_arm_cm DECIMAL(5,1),
    left_thigh_cm DECIMAL(5,1),
    right_thigh_cm DECIMAL(5,1),
    calves_cm DECIMAL(5,1),
    neck_cm DECIMAL(5,1),
    shoulders_cm DECIMAL(5,1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_body_measurements_user ON body_measurements(user_id, measured_at DESC);
