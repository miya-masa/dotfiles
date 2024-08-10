return {
  { -- Add indentation guides even on blank lines
    'lukas-reineke/indent-blankline.nvim',
    -- Enable `lukas-reineke/indent-blankline.nvim`
    -- See `:help ibl`
    main = 'ibl',
    opts = {
      indent = { char = '┊' },
      exclude = {
        filetypes = { 'help', 'startify', 'dirvish', 'no ft', 'fzf', 'NvimTree', 'markdown', 'dashboard', 'glowpreview' },
      },
    },
  },
}
