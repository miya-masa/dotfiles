return {
  {
    "stevearc/overseer.nvim",
    keys = {
      {
        "<leader>om",
        "<cmd>Make<cr>",
        desc = "Make (default target)",
      },
      {
        "<leader>oM",
        ":Make ",
        desc = "Make (with args)",
      },
    },
    config = function(_, opts)
      local overseer = require("overseer")
      overseer.setup(opts)

      -- 公式レシピ: Asynchronous :Make similar to vim-dispatch
      -- vim.o.makeprg を使うので :set makeprg=cmake\ --build\ build のように変更可能
      vim.api.nvim_create_user_command("Make", function(params)
        local cmd, num_subs = vim.o.makeprg:gsub("%$%*", params.args)
        if num_subs == 0 then
          cmd = cmd .. " " .. params.args
        end
        local task = overseer.new_task({
          cmd = vim.fn.expandcmd(cmd),
          components = {
            { "on_output_quickfix", open = not params.bang, open_height = 8 },
            "default",
          },
        })
        task:start()
      end, {
        desc = "Run your makeprg as an Overseer task",
        nargs = "*",
        bang = true,
      })
    end,
  },
}
