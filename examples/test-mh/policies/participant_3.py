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
                "eth_src": "08:00:27:89:3b:9f"
            },
            "action": 
            {
                "drop": 0
            }
        }
    ]
}