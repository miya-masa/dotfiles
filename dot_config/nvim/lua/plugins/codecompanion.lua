return {
  "olimorris/codecompanion.nvim",
  opts = {
    opts = {
      language = "Japanese",
      display = {
        chat = {
          auto_scroll = false,
          show_header_separator = true,
        },
      },
    },
    adapters = {
      copilot = function()
        return require("codecompanion.adapters").extend("copilot", {
          schema = {
            model = {
              default = "claude-3.7-sonnet",
            },
          },
        })
      end,
    },
    strategies = {
      inline = {
        adapter = "copilot",
      },
      chat = {
        adapter = "copilot",
        roles = {
          llm = function(adapter)
            return "  CodeCompanion (" .. adapter.formatted_name .. ")"
          end,
          user = "  Me",
        },
        tools = {
          ["mcp"] = {
            -- calling it in a function would prevent mcphub from being loaded before it's needed
            callback = function()
              return require("mcphub.extensions.codecompanion")
            end,
            description = "Call tools and resources from the MCP Servers",
          },
        },
      },
    },
    prompt_library = {
      ["Translate to English"] = {
        strategy = "inline",
        description = "選択したテキストを英語に翻訳します",
        opts = {
          short_name = "trans_to_en",
          modes = { "v" },
          adapter = {
            name = "copilot",
            model = "gpt-4o",
          },
        },
        prompts = {
          {
            role = "system",
            content = "あなたは優れた開発者であり、日本語と英語のプロ翻訳者でもあります。",
          },
          {
            role = "user",
            content = "<user_prompt>選択したコードドキュメントを英語に変換してください。</user_prompt>",
          },
        },
      },
    },
  },
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-treesitter/nvim-treesitter",
  },
}
