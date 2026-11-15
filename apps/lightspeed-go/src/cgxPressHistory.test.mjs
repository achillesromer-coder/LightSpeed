import {it,expect} from 'vitest';
import {createPressHistory} from './cgxPressHistory.mjs';
import {emptyComposition,addLayer} from './cgxPressComposition.mjs';
it('undo and redo preserve deleted layers and their hierarchy',()=>{
 let c=addLayer(addLayer(emptyComposition(),'object'),'information');c.layers[1].parent_id='layer-1';
 const h=createPressHistory(c);h.record({...c,layers:[]});expect(h.undo().layers).toEqual(c.layers);expect(h.redo().layers).toHaveLength(0);
});
it('new edits invalidate redo and metadata edits cannot corrupt prior frames',()=>{
 const c=emptyComposition();const h=createPressHistory(c);c.title='edited';h.record(c);expect(h.undo().title).toBe('Untitled composition');c.title='branch';h.record(c);expect(h.canRedo).toBe(false);expect(h.undo().title).toBe('Untitled composition');
});
it('bounds history and shares original source objects across frames',()=>{
 const c=emptyComposition();const a={id:'source',size:1,base64:'immutable'};c.assets=[a];const h=createPressHistory(c,2);
 for(const title of ['one','two','three'])h.record({...c,title});expect(h.depth).toBe(2);expect(h.undo().assets[0]).toBe(a);
});
