if [ ! "$(docker ps -a -q -f name='ubuntu_container')" ]; then
	docker run --name ubuntu_container -itd ubuntu /bin/bash
	docker exec -it ubuntu_container /bin/bash -c 'apt update && apt upgrade -y'
	docker exec -it ubuntu_container /bin/bash -c 'apt install -y git make python3 python3-pip ripgrep curl'
	docker exec -it ubuntu_container /bin/bash -c 'curl https://sh.rustup.rs -sSf | sh -s -- -y'
	docker exec -it ubuntu_container /bin/bash -c 'curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash'
	docker exec -it ubuntu_container /bin/bash -c 'source ~/.bashrc && . ~/.nvm/nvm.sh && nvm install 20'
	docker exec -it ubuntu_container /bin/bash -c 'source ~/.bashrc && . ~/.nvm/nvm.sh && cd ~ && npm install neovim tree-sitter-cli'
	docker exec -it ubuntu_container /bin/bash -c 'curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz'
	docker exec -it ubuntu_container /bin/bash -c 'tar --strip-components 1 -C /usr -xzf nvim-linux64.tar.gz'
	docker exec -it ubuntu_container /bin/bash -c 'pip install pynvim'
	docker exec -it ubuntu_container /bin/bash -c '~/.cargo/bin/cargo install fd-find ripgrep'
	docker exec -it ubuntu_container /bin/bash -c "cd ~ && source ~/.bashrc && . ~/.nvm/nvm.sh && LV_BRANCH='release-1.3/neovim-0.9' bash <(curl -s https://raw.githubusercontent.com/LunarVim/LunarVim/release-1.3/neovim-0.9/utils/installer/install.sh) --no-install-dependencies"
	docker exec -it ubuntu_container bash -c "echo 'export PATH=\"\$PATH:~/.local/bin\"' >> ~/.bashrc"
fi

./terminal_recorder -c 'docker exec -it ubuntu_container bash'
