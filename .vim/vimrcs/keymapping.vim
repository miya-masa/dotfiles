" Normal Mode {{{
nnoremap <F8> :source ~/.config/nvim/init.vim<CR>
nnoremap ZZ <Nop>
nnoremap <Down> gj
nnoremap <Up>   gk
nnoremap j gj
nnoremap k gk
nnoremap h <Left>zv
nnoremap l <Right>zv
nnoremap Y y$
nnoremap <Leader><S-\> :vertical<CR>
nnoremap <Leader>- :split<CR>
" nnoremap <Leader><C-B> :Rooter<CR>:Buffer<CR>
nnoremap <Leader><C-B> :Rooter<CR>:Telescope buffers<CR>
" Do not remove the trailing blank
" nnoremap <Leader><C-R> :Rooter<CR>:Rg
nnoremap <Leader><C-R> :Telescope live_grep<CR>
nnoremap <Leader><C-L> :Telescope grep_string<CR>
" nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-G> :Telescope git_files<CR>
nnoremap <Leader><C-Q> :Telescope quickfix<CR>
nnoremap <Leader><C-Y> :Telescope neoclip<CR>
" nnoremap <Leader><C-F> :Files<CR>
" nnoremap <Leader><C-F> :Files<CR>
" nnoremap <leader><C-L> :Line<CR>
" nnoremap <leader><C-L> :Telescope <CR>
" nnoremap <Leader><C-T> :Tags<CR>
nnoremap <Leader>w :w!<CR>
nnoremap <Leader>tsl V:TranslateVisual<CR>
nnoremap <Leader>tsr V:TranslateReplace<CR>
nnoremap - :NvimTreeToggle<CR>
nnoremap <Leader>y :NvimTreeFindFile<CR>
nnoremap <silent> <Leader>sj :SplitjoinJoin<CR>
nnoremap <silent> <Leader>ss :SplitjoinSplit<CR>
" these "Ctrl mappings" work well when Caps Lock is mapped to Ctrl
" nnoremap <silent> t<C-n> :cd %:p:h<cr>:TestNearest<CR>
nnoremap <silent> t<C-n> :lua require("neotest").run.run()<CR>
nnoremap <silent> ti<C-n> :lua require("neotest").run.run()<CR>
nnoremap <silent> t<C-m> :lua require("neotest").run.stop()<CR>
" nnoremap <silent> t<C-f> :cd %:p:h<cr>:TestFile<CR>
nnoremap <silent> t<C-f> :cd %:p:h<cr>:lua require("neotest").run.run(vim.fn.expand("%"))<CR>
nnoremap <silent> t<C-t> :cd %:p:h<cr>:lua require("neotest").summary.toggle()<CR>
nnoremap <silent> t<C-o> :cd %:p:h<cr>:lua require("neotest").output.open({ enter = true })<CR>
nnoremap <silent>[n <cmd>lua require("neotest").jump.prev({ status = "failed" })<CR>
nnoremap <silent>]n <cmd>lua require("neotest").jump.next({ status = "failed" })<CR>

nnoremap <silent> t<C-l> :cd %:p:h<cr>:TestLast<CR>
nnoremap <silent> t<C-g> :cd %:p:h<cr>:TestVisit<CR>
nmap <C-q> <Plug>(quickrun)<CR>
" Do not remove the trailing blank
" nnoremap gp<Space> :G push 
" nnoremap gp<CR> :G push<CR>
" nnoremap gpf<CR> :G push -f<CR>
" nnoremap gca<CR> :G commit --amend<CR>
" Do not remove the trailing blank
" nnoremap gc<Space> :G commit 
command! G Neogit
nnoremap <leader>p :call print_debug#print_debug()<cr>

" }}}

" Terminal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
" }}}

" Visual Mode {{{
vnoremap <Leader>tsl :TranslateVisual<CR>
vnoremap <Leader>tsr :TranslateReplace<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)
vmap <Leader>gx <Plug>(openbrowser-smart-search)
" }}}

" Commandline Mode {{{
cnoremap <C-H> <BS>
cnoremap <C-F> <Right>
cnoremap <C-B> <Left>
" }}}

" Mapping {{{
map <Leader>cc <Plug>(operator-camelize)
map <Leader>C <Plug>(operator-decamelize)
" }}}
"
map <silent> w <Plug>CamelCaseMotion_w
map <silent> b <Plug>CamelCaseMotion_b
map <silent> e <Plug>CamelCaseMotion_e
map <silent> ge <Plug>CamelCaseMotion_ge
sunmap w
sunmap b
sunmap e
sunmap ge


nnoremap <leader>zf :lua require('telekasten').find_notes()<CR>
nnoremap <leader>zd :lua require('telekasten').find_daily_notes()<CR>
nnoremap <leader>zg :lua require('telekasten').search_notes()<CR>
nnoremap <leader>zz :lua require('telekasten').follow_link()<CR>
nnoremap <leader>zT :lua require('telekasten').goto_today()<CR>
nnoremap <leader>zW :lua require('telekasten').goto_thisweek()<CR>
nnoremap <leader>zw :lua require('telekasten').find_weekly_notes()<CR>
nnoremap <leader>zn :lua require('telekasten').new_note()<CR>
nnoremap <leader>zN :lua require('telekasten').new_templated_note()<CR>
nnoremap <leader>zy :lua require('telekasten').yank_notelink()<CR>
nnoremap <leader>zc :lua require('telekasten').show_calendar()<CR>
nnoremap <leader>zC :CalendarT<CR>
nnoremap <leader>zi :lua require('telekasten').paste_img_and_link()<CR>
nnoremap <leader>zt :lua require('telekasten').toggle_todo()<CR>
nnoremap <leader>zb :lua require('telekasten').show_backlinks()<CR>
nnoremap <leader>zF :lua require('telekasten').find_friends()<CR>
nnoremap <leader>zI :lua require('telekasten').insert_img_link({ i=true })<CR>
nnoremap <leader>zp :lua require('telekasten').preview_img()<CR>
nnoremap <leader>zm :lua require('telekasten').browse_media()<CR>
nnoremap <leader>za :lua require('telekasten').show_tags()<CR>
nnoremap <leader># :lua require('telekasten').show_tags()<CR>
nnoremap <leader>zr :lua require('telekasten').rename_note()<CR>

" on hesitation, bring up the panel
nnoremap <leader>z :lua require('telekasten').panel()<CR>

" we could define [[ in **insert mode** to call insert link
" inoremap [[ <cmd>:lua require('telekasten').insert_link()<CR>
" alternatively: leader [
inoremap <leader>[ <cmd>:lua require('telekasten').insert_link({ i=true })<CR>
inoremap <leader>zt <cmd>:lua require('telekasten').toggle_todo({ i=true })<CR>
inoremap <leader># <cmd>lua require('telekasten').show_tags({i = true})<cr>
