" LSP {{{
autocmd CursorHold * silent call CocActionAsync('highlight')
nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
nmap <silent> gm <Plug>(coc-implementation)
nmap <silent> gr <Plug>(coc-references)
nmap <silent> <Leader>gd <Plug>(coc-definition)
nmap <silent> <Leader>gn <Plug>(coc-declaration)
nmap <silent> <F2> <Plug>(coc-rename)
" Use `[j` and `]j` to navigate diagnostics
nmap <silent> [j <Plug>(coc-diagnostic-prev)
nmap <silent> ]j <Plug>(coc-diagnostic-next)

xmap if <Plug>(coc-funcobj-i)
omap if <Plug>(coc-funcobj-i)
xmap af <Plug>(coc-funcobj-a)
omap af <Plug>(coc-funcobj-a)
xmap ic <Plug>(coc-classobj-i)
omap ic <Plug>(coc-classobj-i)
xmap ac <Plug>(coc-classobj-a)
omap ac <Plug>(coc-classobj-a)

" }}
" Golang {{{
augroup go
  autocmd!
  autocmd BufWritePre *.go :Autoformat
  autocmd FileType go nnoremap <Leader><C-F> :call CocAction('runCommand', 'editor.action.organizeImport')<CR>
  autocmd FileType go command! -nargs=0 GoTagsAdd :CocCommand go.tags.add
  autocmd FileType go command! -nargs=0 GoTagsAddPrompt :CocCommand go.tags.add.prompt
  autocmd FileType go command! -nargs=0 GoInstallGopls :CocCommand go.install.gopls

  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4

  " :GoBuild and :GoTestCompile
  " autocmd FileType go nnoremap <leader>gb :<C-u>call <SID>build_go_files()<CR>
  " :GoTest
  autocmd FileType go nnoremap ]] /^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap [[ ?^func<CR>:nohlsearch<CR>
  autocmd FileType go nnoremap <leader>gt :TestFile<CR>
  " :GoCoverageToggle
  " autocmd FileType go nnoremap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoTestFunc
  autocmd FileType go nnoremap <Leader>gf :TestNearest<CR>
  autocmd FileType go nnoremap <Leader>gs :FillStruct<CR>
  " autocmd FileType go nnoremap <Leader>g<C-g> :GoDeclsDir<CR>
  autocmd Filetype go command! GoRunArgs :!go run % <args>

" GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
  autocmd FileType go nnoremap <silent> <Leader>sj :SplitjoinJoin <CR>
  autocmd FileType go nnoremap <silent> <Leader>ss :SplitjoinSplit <CR>

augroup END
" build_go_files is a custom function that builds or compiles the test file.
" It calls :GoBuild if its a Go file, or :GoTestCompile if it's a test file
" function! s:build_go_files()
"   let l:file = expand('%')
"   if l:file =~# '^\f\+_test\.go$'
"     call go#test#Test(0, 1)
"   elseif l:file =~# '^\f\+\.go$'
"     call go#cmd#Build(0)
"   endif
" endfunction
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
