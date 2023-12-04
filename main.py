from controller import Controller

subscribe_convert = "https://lff.ffli7350.workers.dev/sub?target=clash&url=https%3A%2F%2Fsub3.smallstrawberry.com%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3D9bc87fbdfa69b2af4483afa6f2e4cf70%7Chttps%3A%2F%2Fsub.sanfen017.xyz%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3Dc5b9b22ba5536fb4aa1f73b81effb8bb%26flag%3Dclash%7Chttps%3A%2F%2F2clnzhz.xiaoliyu.xyz%3A8443%2Fapi%2Fv1%2Fclient%2F181c687d64753c4d8fd30823e258dcc8%3Fflag%3Dclashmeta&insert=false&config=https%3A%2F%2Fraw.githubusercontent.com%2Flifeifan38324%2FClashConfig%2Fmain%2Fcfw_convert_config.ini&filename=%E6%9D%8E%E9%9D%9E%E5%87%A1&emoji=true&list=false&tfo=false&scv=true&fdn=false&sort=false&new_name=true"

c = Controller(subscribe_convert=subscribe_convert)
c.output_file()
