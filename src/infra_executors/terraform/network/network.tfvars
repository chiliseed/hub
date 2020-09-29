/// 10.0.0.0/16:
//    10.0.0.0/18 - AZ A
//        10.0.0.0/19 — Private
//        10.0.32.0/19
//               10.0.32.0/20 — Public
//               10.0.48.0/20
//                   10.0.48.0/21 — Protected
//                   10.0.56.0/21 — Spare
//    10.0.64.0/18 — AZ B
//        10.0.64.0/19 — Private
//        10.0.96.0/19
//                10.0.96.0/20 — Public
//                10.0.112.0/20
//                    10.0.112.0/21 — Protected
//                    10.0.120.0/21 — Spare
//    10.0.128.0/18 — AZ C
//        10.0.128.0/19 — Private
//        10.0.160.0/19
//                10.0.160.0/20 — Public
//                10.0.176.0/20
//                    10.0.176.0/21 — Protected
//                    10.0.184.0/21 — Spare
//    10.0.192.0/18 — Spare
//

// Overall vpc subnet
vpc_cidr = "10.0.0.0/16"

//                      us-east-2a    us-east-2b
public_subnet_cidrs = ["10.0.0.0/19", "10.0.64.0/19"] # optional
//                      us-east-2a    us-east-2b
private_subnet_cidrs = ["10.0.32.0/20", "10.0.96.0/20"] # optional

availability_zones = ["us-east-2a", "us-east-2b"] # optional
