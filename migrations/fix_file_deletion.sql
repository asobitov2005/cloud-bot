-- Migration to fix file deletion: allow downloads to persist when file is deleted
-- This changes the foreign key constraint to SET NULL instead of RESTRICT

-- For PostgreSQL
ALTER TABLE downloads 
DROP CONSTRAINT IF EXISTS downloads_file_id_fkey;

ALTER TABLE downloads 
ADD CONSTRAINT downloads_file_id_fkey 
FOREIGN KEY (file_id) 
REFERENCES files(id) 
ON DELETE SET NULL;

-- Note: This allows file deletion while preserving download records
-- Download records will have file_id = NULL after file deletion
-- Total downloads count will remain accurate

