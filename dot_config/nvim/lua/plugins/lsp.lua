return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        -- Disable marksman: it indexes every .md under the workspace root
        -- (incl. .worktrees / vendor with 2000+ files) and pins a CPU core.
        marksman = false,
        gopls = {
          settings = {
            gopls = {
              gofumpt = false,
              analyses = {
                nilness = false,
                unusedparams = false,
                unusedwrite = false,
                useany = false,
              },
              staticcheck = false,
              buildFlags = { "-tags=integration,wireinject" },
            },
          },
        },
      },
    },
  },
}
