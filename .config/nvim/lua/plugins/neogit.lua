local neogit = require('neogit')
neogit.setup {
  kind = "split_above",
  integrations = {
    diffview = true
  }
}


-- command! G Neogit
--
vim.api.nvim_create_user_command('G', 'Neogit', {})
