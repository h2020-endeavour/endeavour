{
  "policy": [
    {
      "removal_cookies": [
        {
          "cookie": 1,
          "match": {
            "tcp_dst": 4321
          },
          "action": {
            "fwd": 0
          }
        },

        {
          "cookie": 2,
          "match": {
            "tcp_dst": 4322
          },
          "action": {
            "fwd": 1
          }
        },

        {
          "cookie": 3,
          "match": {
            "eth_src": "08:00:27:89:3b:9f"
          },
          "action": {
            "fwd": 1
          }
        }

      ]
    },
    {
      "new_policies": [
        {
          "cookie": 1,
          "match": {
            "tcp_dst": 4323
          },
          "action": {
            "fwd": 0
          }
        },
        {
          "cookie": 2,
          "match": {
            "tcp_dst": 4324
          },
          "action": {
            "fwd": 1
          }
        },
        {
          "cookie": 3,
          "match": {
            "eth_src": "08:00:27:89:3b:9f"
          },
          "action": {
            "drop": 0
          }
        }
      ]
    }
  ]
}