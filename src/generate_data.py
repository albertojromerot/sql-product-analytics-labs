import numpy as np, pandas as pd, os
np.random.seed(42)
N_CUSTOMERS=20000; N_EVENTS=300000; N_ORDERS=30000; N_PARTICIPANTS=30000
os.makedirs("data/processed", exist_ok=True)
countries=["CO","US","MX","AR","CL","PE","BR","ES"]
age_bands=["18-24","25-34","35-44","45-54","55-64","65+"]
channels=["organic","paid","referral","partner"]
start=pd.Timestamp.today().normalize()-pd.DateOffset(months=24)
signup=start+pd.to_timedelta(np.random.randint(0,24*30,N_CUSTOMERS),unit="D")
customers=pd.DataFrame({
  "customer_id":np.arange(1,N_CUSTOMERS+1),
  "signup_date":signup,
  "country":np.random.choice(countries,N_CUSTOMERS),
  "age_band":np.random.choice(age_bands,N_CUSTOMERS),
  "channel":np.random.choice(channels,N_CUSTOMERS)
})
order_dates=pd.to_datetime(
  np.random.randint(int(signup.min().value/1e9), int(pd.Timestamp.today().value/1e9), N_ORDERS), unit="s"
)
orders=pd.DataFrame({
  "order_id":np.arange(1,N_ORDERS+1),
  "customer_id":np.random.choice(customers["customer_id"].values,N_ORDERS),
  "order_date":order_dates,
  "revenue_usd":np.round(np.random.gamma(2.5,30.0,N_ORDERS)+5,2)
})
event_types=["page_view","product_view","add_to_cart","checkout"]
event_ts=pd.to_datetime(
  np.random.randint(int(signup.min().value/1e9), int(pd.Timestamp.today().value/1e9), N_EVENTS), unit="s"
)
events=pd.DataFrame({
  "event_id":np.arange(1,N_EVENTS+1),
  "customer_id":np.random.choice(customers["customer_id"].values,N_EVENTS),
  "event_ts":event_ts,
  "event_type":np.random.choice(event_types,N_EVENTS,p=[0.60,0.25,0.10,0.05])
})
n=min(N_PARTICIPANTS,len(customers))
participants=np.random.choice(customers["customer_id"].values,size=n,replace=False)
groups=np.random.choice(["A","B"],size=n)
conv_prob=np.where(groups=="B",0.115,0.10)
converted=(np.random.rand(n)<conv_prob)
marketing=pd.DataFrame({
  "exp_id":np.arange(1,n+1),
  "customer_id":participants,
  "group":groups,
  "converted":converted
})
customers.to_csv("data/processed/customers.csv",index=False)
orders.to_csv("data/processed/orders.csv",index=False)
events.to_csv("data/processed/events.csv",index=False)
marketing.to_csv("data/processed/marketing_experiments.csv",index=False)
print("Generated:",len(customers),"customers;",len(orders),"orders;",len(events),"events;",len(marketing),"marketing rows")
