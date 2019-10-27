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
nmap <silent> [j <Plug>(ale_previous_wrap)
nmap <silent> ]j <Plug>(ale_next_wrap)
nnoremap <silent> <C-q> :QuickRun -outputter message<CR>
nnoremap <Leader><C-B> :Buffer<CR>
cnoreabbrev Ack Ack!
nnoremap <Leader><C-A> :Ack!<Space>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <leader><C-T> :Tags<CR>
nnoremap <leader><C-R> :Fq<CR>
nnoremap <Space><CR> V:!sh<CR>
nnoremap <Leader>tv V:TranslateVisual<CR>
nnoremap <Leader>tvr V:TranslateReplace<CR>
nnoremap - :Ranger<CR>
nmap <silent> <Leader>ig <Plug>IndentGuidesToggle
nmap <silent> <Leader>ie <Plug>IndentGuidesEnable
nmap <silent> <Leader>id <Plug>IndentGuidesDisable
" }}}

" Terminal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
" }}}

" Visual Mode {{{
vnoremap <Space><CR> :!sh<CR>
vnoremap <Leader>tve :TranslateVisual<CR>
vnoremap <Leader>tvre :TranslateReplace<CR>
vnoremap <Leader>tvj :TranslateVisual ja:en<CR>
vnoremap <Leader>tvrj :TranslateReplace ja:en<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)
