import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const [base, destino, directorioPrevisualizaciones] = process.argv.slice(2);
if (!base || !destino) throw new Error('Uso: node crear.mjs <entrega> <archivo.xlsx>');
const previews=directorioPrevisualizaciones||path.join(path.dirname(destino),'previsualizaciones');
await fs.mkdir(previews,{recursive:true});
const jsonl = async n => (await fs.readFile(path.join(base,n+'.jsonl'),'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);
const temas = new Map((await jsonl('temas')).map(t=>[t.id,t]));
const secuencias = (await jsonl('secuencias')).sort((a,b)=>temas.get(a.tema_id).orden-temas.get(b.tema_id).orden);
const manifiesto = JSON.parse(await fs.readFile(path.join(base,'manifiesto.json'),'utf8'));
const wb = Workbook.create();
const nombres=['Resumen','Secuencias','Momentos','Dictamenes','Cambios'];
const hojas=Object.fromEntries(nombres.map(n=>[n,wb.worksheets.add(n)]));
const verde='#1E4D3A',gris='#E9EFEB',rojo='#FCE8E6',ambar='#FFF2CC';
for(const h of Object.values(hojas)){h.showGridLines=false;h.tabColor=verde;}
function tabla(nombre,cabecera,filas,anchos){
 const h=hojas[nombre],n=cabecera.length,fin=5+filas.length;
 h.getRangeByIndexes(4,0,1,n).values=[cabecera];
 if(filas.length) h.getRangeByIndexes(5,0,filas.length,n).values=filas;
 const r=h.getRangeByIndexes(4,0,filas.length+1,n);
 r.format.font={name:'Arial',size:10,color:'#202C25'};
 r.format.verticalAlignment='top';r.format.rowHeight=42;
 r.format.wrapText=true;
 const enc=h.getRangeByIndexes(4,0,1,n);
 enc.format={fill:verde,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:38,
  horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
 anchos.forEach((ancho,i)=>h.getRangeByIndexes(4,i,filas.length+1,1).format.columnWidth=ancho);
 const t=h.tables.add(`A5:${col(n)}${fin}`,true,'Tabla'+nombre);
 t.style='TableStyleMedium4';t.showFilterButton=true;
 // Evitar un estilo azul predefinido: cabecera bosque y bandas neutras explícitas.
 for(let i=0;i<filas.length;i+=2)h.getRangeByIndexes(5+i,0,1,n).format.fill='#F4F7F5';
 r.format.autofitRows();enc.format.rowHeight=38;
 h.freezePanes.freezeRows(5);h.freezePanes.freezeColumns(nombre==='Secuencias'?3:1);
 h.getRange('A2').values=[[nombre==='Secuencias'?'Secuencias por tema':nombre]];
 h.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:verde};
 return h;
}
function col(n){let r='';while(n){n--;r=String.fromCharCode(65+n%26)+r;n=Math.floor(n/26);}return r;}
const secFilas=secuencias.map(s=>{const t=temas.get(s.tema_id);return [
 s.tema_id,s.grado,s.asignatura,t.columnas.Unidad,t.columnas.Procedimental,s.estado,s.autoria_asistida?'Sí':'No',
 s.sesiones_sugeridas,s.duracion_sesion_min,null,'No observado',s.motivos_retencion.join(' / '),s.pendientes.join(' / '),
 s.producto_evaluable,...s.criterios_evaluacion,s.consigna_salida,s.apoyos.join(' / '),s.alternativa_sin_internet,
 t.fuente.archivo,t.fuente.hoja,t.fuente.fila,t.fuente.sha256];});
const sh=tabla('Secuencias',['ID tema','Grado','Disciplina','Unidad actual','Procedimental original','Estado IA',
 'Autoría IA','Sesiones sugeridas','Minutos por sesión','Minutos sugeridos total','Tiempo observado','Motivos de retención',
 'Pendientes','Producto evaluable','Criterio 1','Criterio 2','Criterio 3','Consigna de salida','Apoyos',
 'Alternativa sin internet','Archivo fuente','Hoja fuente','Fila fuente','SHA de la fuente'],
 secFilas,[30,9,22,34,70,29,13,16,16,18,20,60,90,80,60,60,60,80,80,80,80,38,12,70]);
sh.getRange(`J6:J${secFilas.length+5}`).formulas=secFilas.map((_,i)=>[`=H${i+6}*I${i+6}`]);
sh.getRange(`G6:G${secFilas.length+5}`).conditionalFormats.add('containsText',{text:'No',format:{fill:rojo,font:{bold:true,color:'#9C2727'}}});
sh.getRange('A3').values=[['Revisión de IA. Las sesiones son sugeridas; no modifican el horario oficial.']];
const momentos=[];const dict=[];const cambios=[];
for(const s of secuencias){
 for(const m of s.momentos) momentos.push([s.tema_id,s.grado,s.asignatura,m.nombre,m.texto_malla,m.propuesta_ia,m.minutos_planificados,s.estado]);
 for(const etapa of ['ciencia','psicopedagogia','refutacion','final','refutacion_final']){
  const r=s.revisiones[etapa];if(!r)continue;
  dict.push([s.tema_id,s.grado,s.asignatura,etapa,r.rol,r.decision,r.confianza,r.justificacion,
   r.evidencia.map(e=>`${e.campo}: ${e.cita}`).join(' / '),r.pendientes.join(' / ')]);
  for(const c of r.cambios)cambios.push([s.tema_id,s.grado,s.asignatura,etapa,c.campo,c.antes,c.despues,c.motivo,s.estado]);
 }
}
tabla('Momentos',['ID tema','Grado','Disciplina','Momento','Texto original de la malla','Propuesta IA','Minutos orientativos','Estado IA'],momentos,[30,9,22,20,95,95,18,30]);
tabla('Dictamenes',['ID tema','Grado','Disciplina','Etapa','Rol IA','Decisión','Confianza','Justificación','Evidencia literal','Pendientes'],dict,[30,9,22,22,26,30,12,100,100,100]);
tabla('Cambios',['ID tema','Grado','Disciplina','Etapa','Campo','Antes de esta revisión','Propuesta de esta revisión','Motivo','Estado secuencia'],cambios,[30,9,22,22,30,100,100,90,30]);
const res=hojas.Resumen;res.getRange('A2').values=[['Ciencias V3: revisión multiagente']];
res.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:verde};
res.getRange('A3').values=[['2.º–11.º. Autoría asistida por IA; sin ensayo docente observado.']];
res.getRange('A3').format.font={name:'Arial',size:10,color:'#555555'};
res.getRange('A5:E5').values=[['Grado','Temas','Autoría IA','Retenidos','Sesiones propuestas*']];
res.getRange('A6:A15').values=Array.from({length:10},(_,i)=>[i+2]);
const last=secuencias.length+5;
res.getRange('B6:E15').formulas=Array.from({length:10},(_,i)=>{const f=i+6;return [
 `=COUNTIFS(Secuencias!$B$6:$B$${last},A${f})`,
 `=COUNTIFS(Secuencias!$B$6:$B$${last},A${f},Secuencias!$G$6:$G$${last},"Sí")`,
 `=B${f}-C${f}`,
 `=SUMIFS(Secuencias!$H$6:$H$${last},Secuencias!$B$6:$B$${last},A${f})`];});
res.getRange('A16').values=[['Total']];res.getRange('B16:E16').formulas=[['=SUM(B6:B15)','=SUM(C6:C15)','=SUM(D6:D15)','=SUM(E6:E15)']];
res.getRange('A5:E16').format.font={name:'Arial',size:11,color:'#202C25'};
res.getRange('A5:E16').format.rowHeight=28;res.getRange('A5:E16').format.columnWidth=20;
res.getRange('A5:E5').format={fill:verde,font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:40,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};
res.getRange('A16:E16').format.fill=gris;res.getRange('A16:E16').format.font.bold=true;
res.getRange('B6:E16').setNumberFormat('#,##0');
res.getRange('G5').values=[['Cómo leer los estados']];res.getRange('G5').format.font={name:'Arial',size:11,bold:true,color:verde};
res.getRange('G6').values=[['Autoría IA: todos los pases requeridos, sin retención ni confianza baja.']];
res.getRange('G7').values=[['Retenido: conserva el desacuerdo o la limitación concreta.']];
res.getRange('G8').values=[['Las competencias siguen siendo declaraciones de la malla.']];
res.getRange('G9').values=[['La distribución de 55 minutos es una hipótesis para adaptar cada sesión.']];
res.getRange('G10').values=[['* Las sesiones suman propuestas, incluidas las retenidas; no son presupuesto aprobado.']];
res.getRange('G5:G12').format.columnWidth=100;res.getRange('G5:G12').format.font.name='Arial';
res.getRange('G5:G12').format.font.size=10;
res.getRange('A19').values=[['Versión de contenido']];res.getRange('B19').values=[[manifiesto.version_contenido]];
res.getRange('A20').values=[['Contrato']];res.getRange('B20').values=[[manifiesto.version_contrato]];
res.getRange('A22').values=[['Hallazgos y ruta de mejora']];
res.getRange('A22').format.font={name:'Arial',size:12,bold:true,color:verde};
for(const [rango,texto] of [
 ['A23:G24','La revisión amplía las propuestas a todos los grados. El resumen distingue las secuencias sin retenciones de las que conservan objeciones. Una retención registra una limitación o desacuerdo: no significa que el tema esté ausente de la malla.'],
 ['A26:G27','Los reparos incluyen contradicciones científicas entre columnas, objetivos presentes en la rúbrica sin una tarea que los ejercite, y protocolos o datos por completar. El cierre documenta sus correcciones y discrepancias; un voto favorable posterior no elimina una retención anterior.'],
 ['A29:G30','La prioridad es resolver cada reparo en una candidata nueva, completar materiales verificables y distribuir las actividades por sesión. Las etiquetas PISA, TIMSS y de competencias digitales son declaraciones de la malla; su presencia no demuestra ejercitación ni aprendizaje.']
]){const r=res.getRange(rango);r.merge();r.values=[[texto]];
 r.format={font:{name:'Arial',size:11,color:'#202C25'},fill:gris,wrapText:true,verticalAlignment:'center',rowHeight:30};}
wb.recalculate();
const esperados={};for(const s of secuencias){const k=s.grado;esperados[k]??=[0,0,0,0];esperados[k][0]++;esperados[k][1]+=+s.autoria_asistida;esperados[k][2]+=+!s.autoria_asistida;esperados[k][3]+=s.sesiones_sugeridas;}
const original=sh.getRange('G6').values[0][0],g=secuencias[0].grado,fila=g+4;
const previo=res.getRange(`C${fila}`).values[0][0];
sh.getRange('G6').values=[[original==='Sí'?'No':'Sí']];wb.recalculate();
const posterior=res.getRange(`C${fila}`).values[0][0];
if(posterior!==previo+(original==='Sí'?-1:1))throw new Error('El conteo no recalcula al cambiar una entrada.');
sh.getRange('G6').values=[[original]];wb.recalculate();
for(let grado=2;grado<=11;grado++){
 const actual=res.getRange(`B${grado+4}:E${grado+4}`).values[0];
 if(JSON.stringify(actual)!==JSON.stringify(esperados[grado]))throw new Error(`Conciliación grado ${grado}: ${actual} != ${esperados[grado]}`);
}
const totales=Object.values(esperados).reduce((a,f)=>a.map((v,i)=>v+f[i]),[0,0,0,0]);
if(JSON.stringify(res.getRange('B16:E16').values[0])!==JSON.stringify(totales))throw new Error('Totales sin conciliar.');
const minutos=sh.getRange(`J6:J${last}`).values;
if(minutos.some((f,i)=>f[0]!==secuencias[i].sesiones_sugeridas*55))throw new Error('Minutos sugeridos sin conciliar.');
console.log((await wb.inspect({kind:'table',range:'Resumen!A5:E16',include:'values,formulas',tableMaxRows:12,tableMaxCols:5,maxChars:2500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
await fs.mkdir(path.dirname(destino),{recursive:true});
for(const [n,rango] of [['Resumen','A1:G30'],['Secuencias','A4:G8'],['Momentos','A4:F7'],['Dictamenes','A4:H7'],['Cambios','A4:H7']]){
 const imagen=await wb.render({sheetName:n,range:rango,scale:1,format:'png'});
 await fs.writeFile(path.join(previews,n+'.png'),new Uint8Array(await imagen.arrayBuffer()));
}
const archivo=await SpreadsheetFile.exportXlsx(wb);await archivo.save(destino);
await fs.writeFile(path.join(path.dirname(destino),'VERIFICACION_EXCEL.json'),JSON.stringify({id_entrega:manifiesto.id_entrega,version_contenido:manifiesto.version_contenido,sha256_xlsx:createHash('sha256').update(await fs.readFile(destino)).digest('hex'),temas:secuencias.length,momentos:momentos.length,dictamenes:dict.length,cambios:cambios.length,conteos:esperados,recalculo_comprobado:true}));
console.log(destino);
