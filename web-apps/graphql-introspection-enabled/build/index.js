const { ApolloServer, gql } = require('apollo-server');

// A trivial schema. The only variable is whether introspection is enabled,
// driven by the INTROSPECTION env var (set per state).
const typeDefs = gql`
  type Query {
    hello: String
  }
`;
const resolvers = { Query: { hello: () => 'world' } };

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.INTROSPECTION === '1',
});

server.listen({ host: '0.0.0.0', port: 4000 }).then(({ url }) => {
  console.log(`ready at ${url}`);
});
