products = db.getSiblingDB('products');
products.createCollection('savings');

products.savings.insertOne({});

products.createUser({
  user: "finchat",
  pwd: "finchat1234",
  roles: [
    {
      role: "readWrite",
      db: "products"
    }
  ]
});
