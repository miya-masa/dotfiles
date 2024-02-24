return {
  'NeogitOrg/neogit',
  dependencies = {
    'nvim-lua/plenary.nvim',  -- required
    'sindrets/diffview.nvim', -- optional - Diff integration

    -- Only one of these is needed, not both.
    'nvim-telescope/telescope.nvim', -- optional
  },
  config = function()
    local neogit = require 'neogit'
    neogit.setup {
      kind = 'split_above',
      integrations = {
        diffview = true,
      },
    }
    -- command! G Neogit
    --
    vim.keymap.set('n', '<leader>G', ':Neogit<CR>')
  end,
}
