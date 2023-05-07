-- Set up nvim-cmp.
local cmp = require 'cmp'

local has_words_before = function()
  unpack = unpack or table.unpack
  local line, col = unpack(vim.api.nvim_win_get_cursor(0))
  return col ~= 0 and vim.api.nvim_buf_get_lines(0, line - 1, line, true)[1]:sub(col, col):match("%s") == nil
end

local feedkey = function(key, mode)
  vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes(key, true, true, true), mode, true)
end

cmp.setup({
  preselect = cmp.PreselectMode.None,
  snippet = {
    -- REQUIRED - you must specify a snippet engine
    expand = function(args)
      vim.fn["vsnip#anonymous"](args.body) -- For `vsnip` users.
      -- require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
      -- require('snippy').expand_snippet(args.body) -- For `snippy` users.
      -- vim.fn["UltiSnips#Anon"](args.body) -- For `ultisnips` users.
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
    ['<C-f>'] = cmp.mapping.scroll_docs(4),
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<C-e>'] = cmp.mapping.abort(),
    ['<CR>'] = cmp.mapping.confirm({ select = true }), -- Accept currently selected item. Set `select` to `false` to only confirm explicitly selected items.
    ["<Tab>"] = cmp.mapping(function(fallback)
      if cmp.visible() then
        cmp.select_next_item()
      elseif vim.fn["vsnip#available"](1) == 1 then
        feedkey("<Plug>(vsnip-expand-or-jump)", "")
      elseif has_words_before() then
        cmp.complete()
      else
        fallback() -- The fallback function sends a already mapped key. In this case, it's probably `<Tab>`.
      end
    end, { "i", "s" }),

    ["<S-Tab>"] = cmp.mapping(function()
      if cmp.visible() then
        cmp.select_prev_item()
      elseif vim.fn["vsnip#jumpable"](-1) == 1 then
        feedkey("<Plug>(vsnip-jump-prev)", "")
      end
    end, { "i", "s" }),
  }),
  window = {
    -- completion = cmp.config.window.bordered(),
    -- documentation = cmp.config.window.bordered(),
  },
  sources = cmp.config.sources({
    { name = 'nvim_lsp' },
    { name = 'vsnip' },
    { name = 'git' },
    -- { name = 'ultisnips'}, -- For ultisnips users.
    { name = 'path' },
    { name = 'calc' },
    { name = 'emoji' },
    { name = 'dictionary', keyword_length = 2 },
  }, {
    { name = 'buffer' },
  })
})

-- Set configuration for specific filetype.
cmp.setup.filetype({ 'gitcommit', 'NeogitCommitMessage' }, {
  sources = cmp.config.sources({
    { name = 'nvim_lsp' },
    { name = 'vsnip' },
    { name = 'git' }, -- You can specify the `cmp_git` source if you were installed it.
    { name = 'cmp_git' }, -- You can specify the `cmp_git` source if you were installed it.
    { name = 'path' },
    { name = 'calc' },
    { name = 'dictionary', keyword_length = 2 },
  }, {
    { name = 'buffer' },
  })
})

-- Use buffer source for `/` and `?` (if you enabled `native_menu`, this won't work anymore).
cmp.setup.cmdline({ '/', '?' }, {
  mapping = cmp.mapping.preset.cmdline(),
  sources = {
    { name = 'buffer' }
  }
})

-- Use cmdline & path source for ':' (if you enabled `native_menu`, this won't work anymore).
cmp.setup.cmdline(':', {
  mapping = cmp.mapping.preset.cmdline(),
  sources = cmp.config.sources({
    { name = 'path' }
  }, {
    { name = 'cmdline' }
  })
})


vim.keymap.set({ 'n', 's', 'i' }, '<C-y>',
  function() return vim.fn['vsnip#expandable']() and '<Plug>(vsnip-expand)' or '<C-y>' end,
  { expr = true })
vim.keymap.set({ 'n', 's', 'i' }, '<C-j>',
  function() return vim.fn['vsnip#available'](1) and '<Plug>(vsnip-expand-or-jump)' or '<C-j>' end, { expr = true })
vim.keymap.set({ 'i', 's' }, '<Tab>',
  function() return vim.fn['vsnip#jumpable'](1) and '<Plug>(vsnip-jump-next)' or '<Tab>' end,
  { expr = true })
vim.keymap.set({ 'i', 's' }, '<S-Tab>',
  function() return vim.fn['vsnip#jumpable'](-1) and '<Plug>(vsnip-jump-prev)' or '<S-Tab>' end,
  { expr = true })

vim.g.vsnip_filetypes = {
  javascriptreact = { 'javascript' },
  typescriptreact = { 'typescript' },
  telekasten = { 'markdown' },
}

require("cmp_git").setup()
