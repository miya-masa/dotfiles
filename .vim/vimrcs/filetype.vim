" LSP {{{
nmap <silent> [j :LspPreviousDiagnostic<cr>
nmap <silent> ]j :LspNextDiagnostic<cr>
" autocmd FileType go nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
nmap <silent> <Leader>gi :LspHover<CR>
" autocmd FileType go nmap <silent> gm <Plug>(coc-implementation)
nmap <silent> gm :LSPImplementation<cr>
" autocmd FileType go nmap <silent> gr <Plug>(coc-references)
nmap <silent> gr :LSPReference<cr>
" autocmd FileType go nmap <silent> <Leader>gd <Plug>(coc-definition)
nmap <silent> <Leader>gd :LspDefinition<cr>
nmap <silent> <Leader>gn :LspDeclaration<cr>
" autocmd FileType go nmap <silent> <F2> <Plug>(coc-rename)
nmap <silent> <F2> :LspRename<cr>
" autocmd FileType go nmap <silent> <Leader><C-F> :GoImports<CR>
" autocmd FileType go nmap <silent> <Leader><C-F> :Format <CR>
nmap <silent> <Leader><C-F> :LspDocumentFormat<cr>
" }}
" Golang {{{
augroup go
  autocmd!
  " autocmd FileType go command! -nargs=0 Format :call CocAction('format')
  " autocmd FileType go command! -nargs=0 Format :call CocAction('format')
  " autocmd FileType go command! -nargs=0 GoTagsAdd :CocCommand go.tags.add
  " autocmd FileType go command! -nargs=0 GoTagsAddPrompt :CocCommand go.tags.add.prompt
  " autocmd FileType go command! -nargs=0 GoInstallGopls :CocCommand go.install.gopls

  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead FileType go setlocal noexpandtab tabstop=4 shiftwidth=4
  " autocmd BufWritePre *.go :Format
  " autocmd BufWritePre *.go :call CocAction('runCommand', 'editor.action.organizeImport')
  autocmd BufWritePre *.go :LspCodeAction source.organizeImports

  " :GoBuild and :GoTestCompile
  autocmd FileType go nmap <leader>gb :<C-u>call <SID>build_go_files()<CR>
  " :GoTest
  autocmd FileType go nmap <leader>gt :GoTest!<CR>
  " :GoCoverageToggle
  autocmd FileType go nmap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoTestFunc
  autocmd FileType go nmap <Leader>gf :GoTestFunc!<CR>
  autocmd FileType go nnoremap <Leader>gs :GoFillStruct<CR>
  autocmd FileType go nnoremap <Leader>g<C-g> :GoDeclsDir<CR>
  autocmd Filetype go command! GoRunArgs :!go run % <args>

" GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
  autocmd FileType go nmap <silent> <Leader>sj :SplitjoinJoin <CR>
  autocmd FileType go nmap <silent> <Leader>ss :SplitjoinSplit <CR>

augroup END
" build_go_files is a custom function that builds or compiles the test file.
" It calls :GoBuild if its a Go file, or :GoTestCompile if it's a test file
function! s:build_go_files()
  let l:file = expand('%')
  if l:file =~# '^\f\+_test\.go$'
    call go#test#Test(0, 1)
  elseif l:file =~# '^\f\+\.go$'
    call go#cmd#Build(0)
  endif
endfunction
" }}}
" Java {{{
  augroup java
    autocmd!
    autocmd FileType java nmap <silent> <Leader>gi :call CocActionAsync("doHover")<CR>
    autocmd FileType java nmap <silent> <Leader>gd <Plug>(coc-definition)
    autocmd FileType java nmap <silent> <Leader>gn <Plug>(coc-declaration)
    autocmd FileType java nmap <silent> <Leader>gr <Plug>(coc-rename)
  augroup END
" }}}
" JSON {{{
  augroup json
    autocmd!
    autocmd FileType json syntax match Comment +\/\/.\+$+
  augroup END
" }}}
" PlantUML {{{
augroup PlantUML
  autocmd!
  au FileType plantuml command! OpenUml :!open -a Google\ Chrome %
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
