return {
  'nvimtools/none-ls.nvim',
  config = function()
    local null_ls = require 'null-ls'
    -- register any number of sources simultaneously
    local sources = {
      null_ls.builtins.formatting.prettier,
      -- null_ls.builtins.diagnostics.golangci_lint,
      null_ls.builtins.diagnostics.hadolint,
      null_ls.builtins.formatting.shfmt,
      null_ls.builtins.diagnostics.rstcheck,
      null_ls.builtins.formatting.pg_format,
      null_ls.builtins.diagnostics.markdownlint.with {
        args = { '--stdin', '-c', vim.fn.expand '$HOME/.markdownlintrc' },
      },
      require 'none-ls.formatting.jq',
      require 'none-ls.formatting.ruff',
      require 'none-ls.diagnostics.ruff',
    }

    null_ls.setup { sources = sources }
  end,
  dependencies = {
    'nvimtools/none-ls-extras.nvim',
  },
}
