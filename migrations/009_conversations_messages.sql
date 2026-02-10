-- Student–Coach messaging: conversations and messages

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    client_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coach_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_user_id, coach_user_id)
);

CREATE INDEX idx_conversations_client ON conversations(client_user_id);
CREATE INDEX idx_conversations_coach ON conversations(coach_user_id);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('client', 'coach')),
    sender_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(conversation_id, created_at DESC);

COMMENT ON TABLE conversations IS 'One conversation per client–coach pair';
COMMENT ON TABLE messages IS 'Chat messages; read_at set when recipient marks as read';
