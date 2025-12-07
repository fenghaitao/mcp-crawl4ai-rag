-- Repositories table to track git repositories containing documentation and source code
CREATE TABLE repositories (
    id BIGSERIAL PRIMARY KEY,
    repo_url TEXT NOT NULL UNIQUE,                     -- Git remote URL (e.g., https://github.com/user/repo.git)
    repo_name TEXT NOT NULL,                           -- Repository name for display (e.g., simics-docs)
    description TEXT,                                  -- Optional description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_repositories_url ON repositories(repo_url);
CREATE INDEX idx_repositories_name ON repositories(repo_name);

-- Comments for documentation
COMMENT ON TABLE repositories IS 'Git repositories containing documentation and source code';
COMMENT ON COLUMN repositories.repo_url IS 'Git remote URL (e.g., https://github.com/user/repo.git)';
COMMENT ON COLUMN repositories.repo_name IS 'Repository name for display (e.g., simics-docs)';
COMMENT ON COLUMN repositories.last_ingested_at IS 'Last time we ingested files from this repository';
