--liquibase formatted sql
--changeset yourname:002-create-transaction-table

CREATE TABLE IF NOT EXISTS transaction
(
    id                  BIGSERIAL PRIMARY KEY,
    wallet_id           BIGINT    NOT NULL REFERENCES wallet (id) ON DELETE CASCADE,
    transaction_type    VARCHAR(8) NOT NULL CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAW')),
    amount              NUMERIC(20, 2) NOT NULL,
    created_at          TIMESTAMP   NOT NULL DEFAULT NOW()
);

--rollback DROP TABLE IF EXISTS transaction;
