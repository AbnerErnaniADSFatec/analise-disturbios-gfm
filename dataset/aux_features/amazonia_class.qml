<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+08" maxScale="0" hasScaleBasedVisibilityFlag="0" version="3.20.3-Odense" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>0</Searchable>
    <Private>0</Private>
  </flags>
  <temporal mode="0" enabled="0" fetchMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option value="false" type="bool" name="WMSBackgroundLayer"/>
      <Option value="false" type="bool" name="WMSPublishDataSourceUrl"/>
      <Option value="0" type="int" name="embeddedWidgets/count"/>
      <Option value="Value" type="QString" name="identify/format"/>
    </Option>
  </customproperties>
  <pipe>
    <provider>
      <resampling enabled="false" zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer band="1" opacity="1" nodataColor="" alphaBand="-1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry label="VEGETACAO NATURAL FLORESTAL PRIMARIA" value="1" color="#005500" alpha="255"/>
        <paletteEntry label="VEGETACAO NATURAL FLORESTAL SECUNDARIA" value="2" color="#0fc80f" alpha="255"/>
        <paletteEntry label="SILVICULTURA" value="9" color="#a8a800" alpha="255"/>
        <paletteEntry label="PASTAGEM ARBUSTIVA/ARBOREA" value="10" color="#e6a04b" alpha="255"/>
        <paletteEntry label="PASTAGEM HERBACEA" value="11" color="#ffec87" alpha="255"/>
        <paletteEntry label="CULTURA AGRICOLA PERENE" value="12" color="#ff8828" alpha="255"/>
        <paletteEntry label="CULTURA AGRICOLA SEMIPERENE" value="13" color="#996400" alpha="255"/>
        <paletteEntry label="CULTURA AGRICOLA TEMPORARIA DE 1 CICLO" value="14" color="#ffe300" alpha="255"/>
        <paletteEntry label="CULTURA AGRICOLA TEMPORARIA DE MAIS DE 1 CICLO" value="15" color="#ffff00" alpha="255"/>
        <paletteEntry label="MINERACAO" value="16" color="#ad89cd" alpha="255"/>
        <paletteEntry label="URBANIZADA" value="17" color="#ffa8c0" alpha="255"/>
        <paletteEntry label="OUTROS USOS" value="20" color="#e1e1e1" alpha="255"/>
        <paletteEntry label="DESFLORESTAMENTO NO ANO" value="22" color="#ff0000" alpha="255"/>
        <paletteEntry label="CORPO DAGUA" value="23" color="#0000ff" alpha="255"/>
        <paletteEntry label="NAO OBSERVADO" value="25" color="#ffffff" alpha="255"/>
        <paletteEntry label="NATURAL NAO FLORESTAL" value="51" color="#b4d79e" alpha="255"/>
      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0" gamma="1"/>
    <huesaturation saturation="0" colorizeRed="255" colorizeBlue="128" colorizeOn="0" grayscaleMode="0" colorizeStrength="100" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
