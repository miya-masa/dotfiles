local null_ls = require("null-ls")

-- register any number of sources simultaneously
local sources = {
  null_ls.builtins.formatting.prettier,
  null_ls.builtins.diagnostics.golangci_lint,
  null_ls.builtins.diagnostics.hadolint,
  null_ls.builtins.diagnostics.markdownlint.with(
    {
      args = { "--stdin", "-c", vim.fn.expand('$HOME/.markdownlintrc') }
    }
  ),
  null_ls.builtins.diagnostics.pyproject_flake8,
  null_ls.builtins.formatting.isort,
  null_ls.builtins.formatting.black,
  null_ls.builtins.code_actions.gitsigns,
}

null_ls.setup({ sources = sources })
