return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
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
