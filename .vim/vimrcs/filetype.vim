" LSP {{{
"
" Having longer updatetime (default is 4000 ms = 4 s) leads to noticeable
" delays and poor user experience.
set updatetime=300

" Don't pass messages to |ins-completion-menu|.
set shortmess+=c

" Always show the signcolumn, otherwise it would shift the text each time
" diagnostics appear/become resolved.
if has("patch-8.1.1564")
  " Recently vim can merge signcolumn and number column into one
  set signcolumn=number
else
  set signcolumn=yes
endif

" Use tab for trigger completion with characters ahead and navigate.
" NOTE: Use command ':verbose imap <tab>' to make sure tab is not mapped by
" other plugin before putting this into your config.
inoremap <silent><expr> <TAB>
      \ pumvisible() ? "\<C-n>" :
      \ <SID>check_back_space() ? "\<TAB>" :
      \ coc#refresh()
inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : "\<C-h>"

function! s:check_back_space() abort
  let col = col('.') - 1
  return !col || getline('.')[col - 1]  =~# '\s'
endfunction

inoremap <silent><expr> <c-x><c-o> coc#refresh()

" Make <CR> auto-select the first completion item and notify coc.nvim to
" format on enter, <cr> could be remapped by other vim plugin
inoremap <silent><expr> <cr> pumvisible() ? coc#_select_confirm()
                              \: "\<C-g>u\<CR>\<c-r>=coc#on_enter()\<CR>"

" Use `[g` and `]g` to navigate diagnostics
" Use `:CocDiagnostics` to get all diagnostics of current buffer in location list.
nmap <silent> [g <Plug>(coc-diagnostic-prev)
nmap <silent> ]g <Plug>(coc-diagnostic-next)

" GoTo code navigation.
nmap <silent> <leader>gd <Plug>(coc-definition)
nmap <silent> <leader>gy <Plug>(coc-type-definition)
nmap <silent> <leader>gi <Plug>(coc-implementation)
nmap <silent> <leader>gr <Plug>(coc-references)

" Use K to show documentation in preview window.
nnoremap <silent> K :call <SID>show_documentation()<CR>

function! s:show_documentation()
  if (index(['vim','help'], &filetype) >= 0)
    execute 'h '.expand('<cword>')
  else
    call CocActionAsync('doHover')
  endif
endfunction

" Highlight the symbol and its references when holding the cursor.
autocmd CursorHold * silent call CocActionAsync('highlight')

" Symbol renaming.
nmap <leader>rn <Plug>(coc-rename)

" Formatting selected code.
xmap <leader><C-F> <Plug>(coc-format-selected)
nmap <leader><C-F> <Plug>(coc-format-selected)

" Applying codeAction to the selected region.
" Example: `<leader>aap` for current paragraph
xmap <leader>a  <Plug>(coc-codeaction-selected)
nmap <leader>a  <Plug>(coc-codeaction-selected)

" Remap keys for applying codeAction to the current buffer.
nmap <leader>ac  <Plug>(coc-codeaction)
" Apply AutoFix to problem on the current line.
nmap <leader>qf  <Plug>(coc-fix-current)

" Map function and class text objects
" NOTE: Requires 'textDocument.documentSymbol' support from the language server.
xmap if <Plug>(coc-funcobj-i)
omap if <Plug>(coc-funcobj-i)
xmap af <Plug>(coc-funcobj-a)
omap af <Plug>(coc-funcobj-a)
xmap ic <Plug>(coc-classobj-i)
omap ic <Plug>(coc-classobj-i)
xmap ac <Plug>(coc-classobj-a)
omap ac <Plug>(coc-classobj-a)

" Use CTRL-S for selections ranges.
" Requires 'textDocument/selectionRange' support of language server.
nmap <silent> <C-s> <Plug>(coc-range-select)
xmap <silent> <C-s> <Plug>(coc-range-select)

" Add `:Format` command to format current buffer.
command! -nargs=0 Format :call CocAction('format')
nnoremap <Leader><C-F> :Format<CR>

" Add `:OR` command for organize imports of the current buffer.
command! -nargs=0 OR   :call CocAction('runCommand', 'editor.action.organizeImport')

" Add (Neo)Vim's native statusline support.
" NOTE: Please see `:h coc-status` for integrations with external plugins that
" provide custom statusline: lightline.vim, vim-airline.
set statusline^=%{coc#status()}%{get(b:,'coc_current_function','')}

"
" }}}
" Golang {{{
augroup go
  autocmd!
  " Add `:OR` command for organize imports of the current buffer.
  autocmd BufWritePre *.go :silent call CocAction('runCommand', 'editor.action.organizeImport')
  autocmd FileType go command! -nargs=0 GoTagsAdd :CocCommand go.tags.add
  autocmd FileType go command! -nargs=0 GoTagsAddPrompt :CocCommand go.tags.add.prompt
  autocmd FileType go command! -nargs=0 GoInstallGopls :CocCommand go.install.gopls
  autocmd FileType go command! -nargs=0 GoGenerate :Dispatch! go generate %:p:h
  autocmd FileType go command! -nargs=0 GoGenerateTest :CocCommand go.test.generate.exported
  autocmd FileType go command! -nargs=0 GoImpl :CocCommand go.impl.cursor

  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4

  " :GoTest
  autocmd FileType go nnoremap ]] /^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap [[ ?^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap <leader>gt :TestFile<CR>
  " :GoCoverageToggle
  " autocmd FileType go nnoremap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoTestFunc
  autocmd FileType go nnoremap <Leader>gf :TestNearest<CR>
  autocmd FileType go nnoremap <Leader>gs :FillStruct<CR>
  autocmd FileType go nnoremap <Leader>gb :GoBuild<CR>
  autocmd Filetype go command! GoRunArgs :Dispatch go run <arg> %
  autocmd Filetype go command! GoRun :Dispatch go run %
  autocmd Filetype go command! GoBuild :Dispatch go build %:p:h

" GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
  autocmd FileType go nnoremap <silent> <Leader>sj :SplitjoinJoin <CR>
  autocmd FileType go nnoremap <silent> <Leader>ss :SplitjoinSplit <CR>
augroup END
" }}}
" JSON {{{
  augroup json
    autocmd!
    autocmd FileType json syntax match Comment +\/\/.\+$+
  augroup END
" }}}
" Javascript {{{
augroup Javascript
  autocmd!
  autocmd FileType javascript let b:javascript_lib_use_underscore = 1
  autocmd FileType javascript let b:javascript_lib_use_react = 1
augroup END
" }}}
" Python {{{
augroup python
  autocmd!
  autocmd Filetype python map <C-F> :call yapf#YAPF()<cr>
  autocmd Filetype python imap <C-F> <c-o>:call yapf#YAPF()<cr>
augroup END
" }}}
" Vim script {{{
augroup vimscript
  autocmd!
  autocmd Filetype vim setlocal foldmethod=marker
  autocmd Filetype vim setlocal foldmarker={{{,}}}
augroup END
" }}}
" Yaml {{{
augroup yaml
  autocmd!
  autocmd Filetype yaml setlocal foldmethod=indent
augroup END
" }}}
