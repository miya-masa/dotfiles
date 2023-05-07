require("mason").setup()
require("mason-lspconfig").setup({
  ensure_installed = { "lua_ls", "rust_analyzer", "gopls", "jsonls", "dockerls", "bashls", "pyright", "yamlls",
    "docker_compose_language_service", "spectral", "sqlls" }
})

-- Mappings.
-- See `:help vim.diagnostic.*` for documentation on any of the below functions
vim.keymap.set('n', '<space>e', vim.diagnostic.open_float)
vim.keymap.set('n', '[g', vim.diagnostic.goto_prev)
vim.keymap.set('n', ']g', vim.diagnostic.goto_next)
vim.keymap.set('n', '<space>q', vim.diagnostic.setloclist)

-- Use an on_attach function to only map the following keys
-- after the language server attaches to the current buffer
local on_attach = function(client, bufnr)
  -- Enable completion triggered by <c-x><c-o>
  vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')

  -- Mappings.
  -- See `:help vim.lsp.*` for documentation on any of the below functions
  vim.keymap.set('n', '<Leader>gD', vim.lsp.buf.declaration)
  vim.keymap.set('n', '<Leader>gd', vim.lsp.buf.definition)
  vim.keymap.set('n', 'K', vim.lsp.buf.hover)
  vim.keymap.set('n', '<Leader>gi', vim.lsp.buf.implementation)
  vim.keymap.set('n', '<Leader><C-k>', vim.lsp.buf.signature_help)
  vim.keymap.set('n', '<Leader>wa', vim.lsp.buf.add_workspace_folder)
  vim.keymap.set('n', '<Leader>wr', vim.lsp.buf.remove_workspace_folder)
  vim.keymap.set('n', '<Leader>wl', function()
    print(vim.inspect(vim.lsp.buf.list_workspace_folders()))
  end)
  vim.keymap.set('n', '<Leader>D', vim.lsp.buf.type_definition)
  vim.keymap.set('n', '<Leader>rn', vim.lsp.buf.rename)
  vim.keymap.set('n', '<Leader>ca', vim.lsp.buf.code_action)
  vim.keymap.set('n', '<Leader>gr', vim.lsp.buf.references)
  vim.keymap.set('n', '<C-f>', function() vim.lsp.buf.format { async = true } end)
end

local lsp_flags = {
  -- This is the default in Nvim 0.7+
  debounce_text_changes = 150,
}

-- Set up lspconfig.
local capabilities = require('cmp_nvim_lsp').default_capabilities(vim.lsp.protocol.make_client_capabilities())
capabilities.textDocument.completion.completionItem.snippetSupport = true

require("mason-lspconfig").setup_handlers({
  -- The first entry (without a key) will be the default handler
  -- and will be called for each installed server that doesn't have
  -- a dedicated handler.
  function(server_name) -- default handler (optional)
    require("lspconfig")[server_name].setup {
      on_attach = on_attach,
      capabilities = capabilities,
      flags = lsp_flags,
    }
  end,
  -- Next, you can provide targeted overrides for specific servers.
  ["gopls"] = function()
    require("lspconfig").gopls.setup {
      on_attach = on_attach,
      capabilities = capabilities,
      settings = {
        gopls = {
          buildFlags = { "-tags=integration" },
          gofumpt = true,
          usePlaceholders = true,
        }
      },
    }
  end,
  ["lua_ls"] = function()
    require("lspconfig").lua_ls.setup {
      on_attach = on_attach,
      capabilities = capabilities,
      settings = {
        Lua = {
          runtime = {
            -- Tell the language server which version of Lua you're using (most likely LuaJIT in the case of Neovim)
            version = 'LuaJIT',
          },
          diagnostics = {
            -- Get the language server to recognize the `vim` global
            globals = { 'vim' },
          },
          workspace = {
            -- Make the server aware of Neovim runtime files
            library = vim.api.nvim_get_runtime_file("", true),
            checkThirdParty = false,
          },
          -- Do not send telemetry data containing a randomized but unique identifier
          telemetry = {
            enable = false,
          },
        },
      },
    }
  end,
})
