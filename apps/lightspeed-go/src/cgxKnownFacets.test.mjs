import {it,expect} from 'vitest';
import {emptyComposition,sourceAsset,addAsset,addLayer} from './cgxPressComposition.mjs';
import {resolveKnownFacets,readKnownFacet} from './cgxKnownFacets.mjs';
it('resolves one source object across multiple presentation facets without copying source bodies',async()=>{
 const a=await sourceAsset('fact.txt','text/plain',new TextEncoder().encode('Source fact'));
 let c=addAsset(emptyComposition(),a).composition;c=addLayer(addLayer(c,'information',a.id),'object',a.id);
 const r=await resolveKnownFacets(c);expect(r.objects).toHaveLength(1);expect(r.objects[0].presentation_facets).toHaveLength(2);
 expect(r.source_body_copies).toBe(0);expect(readKnownFacet(r,'sha256:'+a.id,'source_text_preview')).toBe('Source fact');
 expect(()=>readKnownFacet(r,'sha256:'+a.id,'physical_geometry')).toThrow('FACET_UNKNOWN_OR_UNVERIFIED');
 expect(()=>readKnownFacet(r,'invented','source_name')).toThrow('SOURCE_OBJECT_UNRESOLVED');
});
it('never promotes display annotations into known source facts',async()=>{
 const c=addLayer(emptyComposition(),'information');c.layers[0].text='Invented source fact';
 const r=await resolveKnownFacets(c);expect(r.objects).toHaveLength(0);expect(r.display_only_layers).toHaveLength(1);expect(r.native_mint).toBe(false);
});
