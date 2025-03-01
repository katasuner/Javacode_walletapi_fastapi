--liquibase formatted sql
--changeset yourname:003_create_index_walletuuid

CREATE INDEX idx_wallet_uuid ON wallet(wallet_uuid);

--rollback DROP INDEX IF EXISTS idx_wallet_uuid;