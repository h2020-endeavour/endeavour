## Operator use cases

| Name                      | Direct from iSDX\Umbrella | Monitoring dependant |                                       Status                                      |
|---------------------------|---------------------------|----------------------|:---------------------------------------------------------------------------------:|
| Access Control            |            Yes            |          No          | With and iSDX and Umbrella implemented,  this use case should be straight forward |
| Network Resource Security |             No            |          No          |                                    Not started                                    |
| Broadcast Prevention      |            Yes            |          No          |                 Umbrella is implemented, thus use case is trivial                 |
| Central Configuration     |             No            |          No          |                                    Not started                                    |
| Adaptive Monitoring       |             No            |          Yes         |                                    Not started                                    |
| Load Balancing            |             No            |          Yes         | Basic LB under implementation                                                     |
| Layer 2 Label Switching   |            Yes            |          No          |                   Basic Umbrella label switching is implemented.                  |

## Participant use cases

| Name                                  | Direct from iSDX\Umbrella | Monitoring dependant |                                                 Status                                                |
|---------------------------------------|---------------------------|----------------------|:-----------------------------------------------------------------------------------------------------:|
| Inbound/Outbound TE                   |            Yes            |          No          |               iSDX should give it automatically.  Needs to decide what examples to show.              |
| Control / Data Plane Consistency      |            Yes            |          No          |               Peering relations are known at the iSDX config.  Thus it is a direct case.              |
| Advanced Blackholing                  |            Yes            |          Yes         | Blackholing policies can be applied using iSDX. Though, monitoring side still needs to be implemented |
| Virtualized Private Peering           |             No            |          No          |                                              Not started                                              |
| Control Plane Traffic Protection      |             No            |          No          |                                              Not started                                              |
| Destination Port Congestion Awareness |             No            |          Yes         |                                              Not started                                              |
