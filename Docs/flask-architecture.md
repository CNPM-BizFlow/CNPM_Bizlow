# Architecture
```bash
bizflow
├── migrations/                 
├── scripts/
│   └── run_postgres.sh         
│
├── src/
│   ├── api/                    
│   │   ├── controllers/        
│   │   │   ├── order_controller.py
│   │   │   ├── product_controller.py
│   │   │   └── auth_controller.py
│   │   │
│   │   ├── schemas/            
│   │   │   ├── order_schema.py
│   │   │   └── product_schema.py
│   │   │
│   │   ├── middleware.py
│   │   ├── requests.py
│   │   └── responses.py
│   │
│   ├── domain/                 
│   │   ├── models/
│   │   │   ├── user.py         
│   │   │   ├── store.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   ├── customer.py
│   │   │   └── debt.py
│   │   │
│   │   ├── constants.py        
│   │   └── exceptions.py
│   │
│   ├── services/               
│   │   ├── create_order_service.py
│   │   ├── confirm_draft_order_service.py
│   │   ├── record_debt_service.py
│   │   └── report_service.py
│   │
│   ├── infrastructure/        
│   │   ├── databases/
│   │   │   ├── db.py  
│   │   │   └── .....                  
│   │   │                
│   │   │
│   │   ├── models/             
│   │   │   ├── user_model.py
│   │   │   ├── store_model.py
│   │   │   ├── product_model.py
│   │   │   ├── order_model.py
│   │   │   ├── order_item_model.py
│   │   │   └── customer_model.py
│   │   │
│   │   ├── repositories/       
│   │   │   ├── order_repository.py 
│   │   │   ├── product_repository.py
│   │   │   └── customer_repository.py
│   │   │
│   │   └── services/           
│   │       └── ai_service.py
│   │
│   ├── app.py
│   ├── create_app.py
│   ├── config.py
│   ├── dependency_container.py
│   ├── error_handler.py
│   └── logging.py
│
└── README.md
```