{
    "inbound": [
        {
            "cookie": 1,
            "match": 
            {
                "tcp_dst": 4321
            },
            "action": 
            {
                "fwd": 0
            }
        },
        {
            "cookie": 2,
            "match": 
            {
                "tcp_dst": 4322
            },
            "action": 
            {
                "fwd": 1
            }
        },
         {
            "cookie": 3,
            "match": 
            {
                "ip_src": 100.0.0.1
            },
            "action": 
            {
                "drop": 0
            }
        }
    ]
}