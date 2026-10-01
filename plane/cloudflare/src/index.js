export default {
 async fetch(req, env){
  const url=new URL(req.url);
  if(url.pathname.startsWith('/api/')||url.pathname.startsWith('/ledger/')){
    return new Response('401 Unauthorized at edge — bounded', {status:401, headers:{'Cache-Control':'no-store'}});
  }
  return env.ASSETS.fetch(req);
 }
}