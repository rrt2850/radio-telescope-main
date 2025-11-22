
Don't use ngrok it kind of sucks, just keeping this here in case we want it in the future
Exposing the ip to the public through ngrok (different url every time):
- install ngrok on the pi you want to use 
- go to dashboard.ngrok.com and set up an account
- it'll take you to https://dashboard.ngrok.com/get-started/setup/linux where you have to follow the instructions
    - If you use the browser on the radioastro pi, it'll probably look super buggy. Good luck!
- run ngrok http 8000 to link the local ip to the already linked ngrok account
- You're all set!


IF YOU'RE IN A TIME CRUNCH, DO THIS AS SOON AS POSSIBLE.
IT CAN TAKE A WHILE FOR EVERYTHING TO GET SET UP.
Creating a cloudfare access point:
- Get a custom domain, ours is spex-telescope-backend.online
- Set up a cloudfare account
- For your domain, change the nameservers to the ones from your cloudfare account
- on the domain manager, make sure dnssec is disabled
- install cloudflared localally on the pi. for debian, I used this command:
    sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg /dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt-get update && sudo apt-get install cloudflared   
- Do cloudflared tunnel login to login to cloudflare on the pi
- Edit the config file in the .cloudflared directory generated, it has sensitive data so I'm not putting it in the git but I'll make a template later.
- Launch the stuff you set up in the config:
    - cloudflared tunnel route dns telescope-api spex-telescope-backend.online
    - cloudflared tunnel run telescope-api