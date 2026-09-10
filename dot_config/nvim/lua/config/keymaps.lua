-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Agent bridge (<leader>a): herdr の隣ペインで走っている Claude Code / Codex と
-- のやり取り。実体は lua/config/agent_bridge.lua。
-- レビュー指摘を書く側は <leader>r (lua/plugins/review.lua) が持つ。
local function bridge(fn)
  return function()
    require("config.agent_bridge")[fn]()
  end
end

vim.keymap.set({ "n", "v" }, "<leader>a", "", { desc = "+agent" })
vim.keymap.set("n", "<leader>ao", bridge("open_review_diff"), { desc = "Open Review Diff (base..worktree)" })
vim.keymap.set("n", "<leader>af", bridge("send_file"), { desc = "Send File to Agent" })
vim.keymap.set("n", "<leader>aF", bridge("send_changed_files"), { desc = "Send Changed Files to Agent" })
vim.keymap.set("x", "<leader>as", bridge("send_selection"), { desc = "Send Selection to Agent" })
vim.keymap.set("n", "<leader>aR", bridge("request_review_response"), { desc = "Request Review Response" })
