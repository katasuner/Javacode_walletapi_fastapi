--liquibase formatted sql
--changeset yourname:001-create-wallet-table

CREATE TABLE IF NOT EXISTS wallet
(
    id              BIGSERIAL PRIMARY KEY,
    wallet_uuid     UUID        NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    balance         NUMERIC(20, 2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

--rollback DROP TABLE IF EXISTS wallet;
