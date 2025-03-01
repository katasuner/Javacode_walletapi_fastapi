--liquibase formatted sql
--changeset yourname:003-add-wallet-uuid-index

CREATE INDEX idx_wallet_uuid ON wallet(wallet_uuid);

--rollback DROP INDEX IF EXISTS idx_wallet_uuid;