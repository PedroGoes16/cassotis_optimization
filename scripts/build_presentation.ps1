$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root 'presentation'
$previewDir = Join-Path $outDir 'preview'
$pptxPath = Join-Path $outDir 'entrega3_apresentacao_padrao_entrega1.pptx'

New-Item -ItemType Directory -Force -Path $outDir, $previewDir | Out-Null

function Color([int]$r, [int]$g, [int]$b) {
    return $r + 256 * $g + 65536 * $b
}

$charcoal = Color 27 31 36
$oxide = Color 180 68 31
$gold = Color 214 154 60
$ink = Color 27 31 36
$muted = Color 94 103 114
$footer = Color 124 139 153
$paper = Color 243 244 246
$white = Color 255 255 255
$line = Color 214 219 225
$soft = Color 232 235 239
$peach = Color 247 226 216
$markerGray = Color 202 208 215
$font = 'Arial'

function Add-Text {
    param($Slide, [double]$X, [double]$Y, [double]$W, [double]$H,
        [string]$Text, [double]$Size = 20, [int]$TextColor = $ink,
        [bool]$Bold = $false, [int]$Align = 1)
    $shape = $Slide.Shapes.AddTextbox(1, $X, $Y, $W, $H)
    $shape.Fill.Visible = 0
    $shape.Line.Visible = 0
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    $shape.TextFrame.WordWrap = -1
    $shape.TextFrame.AutoSize = 0
    $range = $shape.TextFrame.TextRange
    $range.Text = $Text
    $range.Font.Name = $font
    $range.Font.Size = $Size
    $range.Font.Bold = $(if ($Bold) { -1 } else { 0 })
    $range.Font.Color.RGB = $TextColor
    $range.ParagraphFormat.Alignment = $Align
    # PowerPoint may collapse a newly created textbox to one line after text is assigned.
    # Restore the requested geometry so wrapped text remains inside the editable box.
    $shape.Width = $W
    $shape.Height = $H
    return $shape
}

function Add-Rect {
    param($Slide, [double]$X, [double]$Y, [double]$W, [double]$H,
        [int]$FillColor, [double]$Radius = 0, [int]$LineColor = -1, [double]$LineWidth = 1)
    $geometry = $(if ($Radius -gt 0) { 5 } else { 1 })
    $shape = $Slide.Shapes.AddShape($geometry, $X, $Y, $W, $H)
    $shape.Fill.ForeColor.RGB = $FillColor
    $shape.Fill.Solid()
    if ($LineColor -ge 0) {
        $shape.Line.Visible = -1
        $shape.Line.ForeColor.RGB = $LineColor
        $shape.Line.Weight = $LineWidth
    }
    else {
        $shape.Line.Visible = 0
    }
    return $shape
}

function Add-Header {
    param($Slide, [string]$Text, [string]$Section = '')
    Add-Rect $Slide 43 33 9 9 $oxide | Out-Null
    Add-Rect $Slide 55 33 9 9 $oxide | Out-Null
    Add-Rect $Slide 67 33 9 9 $markerGray | Out-Null
    Add-Text $Slide 81 29 820 18 $Section.ToUpper() 10.5 $oxide $true 1 | Out-Null
    Add-Text $Slide 43 58 874 58 $Text 31 $ink $true 1 | Out-Null
}

function Add-Footer {
    param($Slide, [int]$Number, [int]$Total = 9)
    Add-Text $Slide 43 508 760 14 'Otimização de pilhas · Entrega 3' 8.5 $footer $false 1 | Out-Null
    Add-Text $Slide 866 507 50 16 (([string]$Number).PadLeft(2, '0') + ' / ' + ([string]$Total).PadLeft(2, '0')) 9 $footer $false 3 | Out-Null
}

function Add-PictureFit {
    param($Slide, [string]$Path, [double]$X, [double]$Y, [double]$W, [double]$H)
    $picture = $Slide.Shapes.AddPicture($Path, 0, -1, $X, $Y, -1, -1)
    $picture.LockAspectRatio = -1
    $scale = [Math]::Min($W / $picture.Width, $H / $picture.Height)
    $picture.Width = $picture.Width * $scale
    $picture.Height = $picture.Height * $scale
    $picture.Left = $X + ($W - $picture.Width) / 2
    $picture.Top = $Y + ($H - $picture.Height) / 2
    return $picture
}

function Add-Note {
    param($Slide, [string]$Text)
    foreach ($shape in $Slide.NotesPage.Shapes) {
        if ($shape.Type -eq 14 -and $shape.PlaceholderFormat.Type -eq 2) {
            $shape.TextFrame.TextRange.Text = $Text
            return
        }
    }
}

function Add-Step {
    param($Slide, [double]$X, [double]$Y, [double]$W, [string]$Number,
        [string]$Heading, [string]$Body)
    Add-Rect $Slide $X $Y $W 112 $white 0 $line 0.8 | Out-Null
    Add-Rect $Slide ($X + 18) ($Y + 18) 28 28 $oxide | Out-Null
    Add-Text $Slide ($X + 18) ($Y + 20) 28 24 $Number 14 $white $true 2 | Out-Null
    Add-Text $Slide ($X + 58) ($Y + 18) ($W - 76) 26 $Heading 15.5 $ink $true 1 | Out-Null
    Add-Text $Slide ($X + 18) ($Y + 56) ($W - 36) 42 $Body 12.5 $muted $false 1 | Out-Null
}

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = -1
$ppt.WindowState = 2
$pres = $ppt.Presentations.Add()
$pres.PageSetup.SlideWidth = 960
$pres.PageSetup.SlideHeight = 540

try {
    # 1. Cover
    $slide = $pres.Slides.Add(1, 12)
    Add-Rect $slide 0 0 960 540 $charcoal | Out-Null
    Add-Rect $slide 58 65 9 9 $oxide | Out-Null
    Add-Rect $slide 70 65 9 9 $oxide | Out-Null
    Add-Rect $slide 82 65 9 9 (Color 55 63 72) | Out-Null
    Add-Text $slide 99 61 760 18 'UFMG · TEORIA DA DECISÃO · 2026/2 · ENTREGA 3 · NOVEMBRO 2026' 10.5 $gold $true 1 | Out-Null
    Add-Text $slide 58 118 500 144 'Otimização e decisão multicritério de pilhas de minério' 34 $white $true 1 | Out-Null
    Add-Text $slide 58 292 470 48 'GVNS, otimização multiobjetivo e recomendação final' 17 (Color 160 170 181) $false 1 | Out-Null
    $coverPattern = @(
        '2010010010','1002001010','0100102000','0012010010','1201000201',
        '0100010120','0010201001','1002100102','0210001020','2100102012'
    )
    for ($r = 0; $r -lt 10; $r++) {
        Add-Text $slide 568 (112 + $r * 24) 28 16 ('P' + ($r + 1)) 9.5 (Color 158 168 178) $false 3 | Out-Null
        for ($c = 0; $c -lt 10; $c++) {
            $digit = [int][string]$coverPattern[$r][$c]
            $fill = $(if ($digit -eq 1) { $oxide } elseif ($digit -eq 2) { $gold } else { Color 55 63 72 })
            Add-Rect $slide (604 + $c * 18) (111 + $r * 24) 14 14 $fill | Out-Null
        }
    }
    Add-Text $slide 604 360 260 18 '10 pilhas · 145 caminhões de 2 kt' 10.5 (Color 160 170 181) $false 1 | Out-Null
    Add-Rect $slide 58 402 844 1 (Color 55 63 72) | Out-Null
    Add-Text $slide 58 426 200 16 'GRUPO' 9.5 (Color 160 170 181) $true 1 | Out-Null
    Add-Text $slide 58 446 210 62 "Allan Melquíades · Diogo Muzzi`nGabriel Ramos · Pedro Goes`nPedro Vieira · Vitor Hugo Lacerda Lana" 9.5 $gold $false 1 | Out-Null
    Add-Text $slide 302 426 160 16 'INSTÂNCIA' 9.5 (Color 160 170 181) $true 1 | Out-Null
    Add-Text $slide 302 446 160 40 "20 minérios · 10 pilhas`n290 kt" 11.5 (Color 224 228 233) $false 1 | Out-Null
    Add-Text $slide 520 426 160 16 'ANÁLISE FINAL' 9.5 (Color 160 170 181) $true 1 | Out-Null
    Add-Text $slide 520 446 175 40 "91 alternativas`n2 métodos multicritério" 11.5 (Color 224 228 233) $false 1 | Out-Null
    Add-Text $slide 734 426 160 16 'RECOMENDAÇÃO' 9.5 (Color 160 170 181) $true 1 | Out-Null
    Add-Text $slide 734 446 150 40 "A073`nrobusta em 15 cenários" 11.5 (Color 224 228 233) $false 1 | Out-Null
    Add-Note $slide "Tempo: 20 segundos.`nApresentar o objetivo geral: transformar um problema operacional de composição de pilhas em uma recomendação final reproduzível. Antecipar que a solução combina GVNS, duas abordagens multiobjetivo e dois métodos multicritério."

    # 2. Problem
    $slide = $pres.Slides.Add(2, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Dez pilhas acopladas por uma disponibilidade global' 'O problema e a formulação' | Out-Null
    Add-Text $slide 43 128 874 32 '145 caminhões de 2 kt · 290 kt distribuídas em dez pilhas · três objetivos minimizados' 15.5 $ink $false 1 | Out-Null
    Add-Rect $slide 43 178 370 270 $white 0 $line 0.8 | Out-Null
    Add-Text $slide 65 198 320 22 'DECISÃO E RESTRIÇÕES' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 65 238 310 36 'xᵢₚ = número de caminhões do minério i na pilha p' 16 $ink $true 1 | Out-Null
    Add-Text $slide 65 296 300 102 "Massa fixa e integralidade`nElegibilidade por grupo`nDisponibilidade global`nFaixas químicas de SiO₂ e Al₂O₃" 14 $ink $false 1 | Out-Null
    Add-Text $slide 65 408 300 26 'f1 custo · f2 SiO₂ · f3 Al₂O₃' 14 $oxide $true 1 | Out-Null
    $masses = @(20,22,24,26,28,30,32,34,36,38)
    for ($i = 0; $i -lt 10; $i++) {
        $x = 464 + $i * 43
        $h = $masses[$i] * 5.4
        $fill = $(if ($i % 3 -eq 0) { $oxide } elseif ($i % 3 -eq 1) { $gold } else { Color 55 63 72 })
        Add-Rect $slide $x (434 - $h) 28 $h $fill | Out-Null
        Add-Text $slide ($x - 4) 443 36 18 ('P' + ($i + 1)) 9 $muted $true 2 | Out-Null
        Add-Text $slide ($x - 4) (411 - $h) 36 18 ([string]$masses[$i]) 9 $ink $true 2 | Out-Null
    }
    Add-Text $slide 464 178 420 24 'MASSA DAS PILHAS (kt)' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 464 474 410 18 'P1–P5: Sinter 1 · P6–P10: Sinter 2' 10 $muted $false 2 | Out-Null
    Add-Footer $slide 2
    Add-Note $slide "Tempo: 50 segundos.`nExplicar que a decisão aloca caminhões de minérios às dez pilhas. A representação preserva massa e integralidade. Destacar o conflito: reduzir custo costuma afastar a composição dos alvos químicos. Não detalhar todas as equações."

    # 3. Algorithm
    $slide = $pres.Slides.Add(3, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'GVNS: decisões e protocolo experimental' 'O algoritmo completo' | Out-Null
    Add-Step $slide 43 142 205 '1' 'Construtiva' 'Atende mínimos globais e elegibilidade.'
    Add-Step $slide 267 142 205 '2' 'VND' 'Primeira melhoria em N1, N2 e N3.'
    Add-Step $slide 491 142 205 '3' 'SHAKE' 'Perturbações P1, P2 e P3 fora da VND.'
    Add-Step $slide 715 142 202 '4' 'Aceitação' 'Melhoria estrita pela regra de viabilidade.'
    Add-Rect $slide 43 282 874 46 $soft | Out-Null
    Add-Text $slide 62 296 838 24 'N1 completa · N2/N3 amostradas sem reposição · parâmetros e seeds congelados antes da rodada oficial' 13 $ink $true 1 | Out-Null
    Add-Rect $slide 43 350 874 128 $charcoal | Out-Null
    Add-Text $slide 62 366 820 18 'CONFIGURAÇÃO FINAL' 10.5 $gold $true 1 | Out-Null
    Add-Text $slide 62 398 154 36 '200.000' 25 $white $true 1 | Out-Null
    Add-Text $slide 62 436 170 20 'avaliações por execução' 11 (Color 204 210 218) $false 1 | Out-Null
    Add-Text $slide 290 398 94 36 '250' 25 $white $true 1 | Out-Null
    Add-Text $slide 290 436 170 20 'movimentos amostrados' 11 (Color 204 210 218) $false 1 | Out-Null
    Add-Text $slide 522 398 150 36 '3 / 4 / 5' 25 $white $true 1 | Out-Null
    Add-Text $slide 522 436 170 20 'força de P1 / P2 / P3' 11 (Color 204 210 218) $false 1 | Out-Null
    Add-Text $slide 760 398 70 36 '5' 25 $white $true 1 | Out-Null
    Add-Text $slide 760 436 120 20 'seeds oficiais' 11 (Color 204 210 218) $false 1 | Out-Null
    Add-Footer $slide 3
    Add-Note $slide "Tempo: 60 segundos.`nApresentar o ciclo da GVNS. N1 substitui um minério, N2 troca minérios entre pilhas e N3 faz realocação em cadeia. A regra de viabilidade permite começar inviável e prioriza encontrar factibilidade. Mencionar que parâmetros e seeds foram congelados antes das rodadas oficiais."

    # 4. Multiobjective
    $slide = $pres.Slides.Add(4, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Duas abordagens cobrem regiões diferentes' 'Otimização multiobjetivo' | Out-Null
    $img1 = Join-Path $root 'results\multi_final\pareto_weighted_sum_f1_f2.png'
    $img2 = Join-Path $root 'results\multi_final\pareto_epsilon_restricted_f1_f2.png'
    Add-Rect $slide 43 136 424 286 $white 0 $line 0.8 | Out-Null
    Add-Rect $slide 493 136 424 286 $white 0 $line 0.8 | Out-Null
    Add-PictureFit $slide $img1 53 146 404 266 | Out-Null
    Add-PictureFit $slide $img2 503 146 404 266 | Out-Null
    Add-Text $slide 62 428 386 22 'SOMA PONDERADA · 45 VETORES' 11 $oxide $true 2 | Out-Null
    Add-Text $slide 512 428 386 22 'ε-RESTRITO · 49 VETORES' 11 $oxide $true 2 | Out-Null
    Add-Rect $slide 43 462 874 32 $soft | Out-Null
    Add-Text $slide 60 469 840 20 '160 execuções oficiais · 91 composições conjuntamente não dominadas' 13.5 $ink $true 2 | Out-Null
    Add-Footer $slide 4
    Add-Note $slide "Tempo: 60 segundos.`nExplicar que cada abordagem usa 16 configurações e cinco seeds. A Soma Ponderada alcançou extremos químicos mais fortes; o epsilon-restrito concentrou soluções em faixas controladas. Ressaltar que a cobertura depende das grades e que as frentes são aproximações."

    # 5. Multicriteria
    $slide = $pres.Slides.Add(5, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Da fronteira de Pareto à escolha final' 'Decisão multicritério' | Out-Null
    Add-Text $slide 43 132 410 24 'QUATRO CRITÉRIOS MINIMIZADOS' 11 $oxide $true 1 | Out-Null
    $criteria = @(
        @('f1','Custo total','R$'),
        @('f2','Desvio quadrático de SiO₂','qualidade'),
        @('f3','Desvio quadrático de Al₂O₃','qualidade'),
        @('H','Heterogeneidade das receitas','operação')
    )
    Add-Rect $slide 43 160 410 254 $white 0 $line 0.8 | Out-Null
    for ($i = 0; $i -lt 4; $i++) {
        $y = 178 + $i * 57
        Add-Text $slide 64 $y 44 30 $criteria[$i][0] 20 $oxide $true 1 | Out-Null
        Add-Text $slide 116 $y 270 22 $criteria[$i][1] 14.5 $ink $true 1 | Out-Null
        Add-Text $slide 116 ($y + 24) 190 17 $criteria[$i][2] 10 $muted $false 1 | Out-Null
        if ($i -lt 3) { Add-Rect $slide 62 ($y + 48) 370 1 $line | Out-Null }
    }
    Add-Text $slide 491 132 426 24 'MÉTODOS COMPLEMENTARES' 11 $oxide $true 1 | Out-Null
    Add-Rect $slide 491 160 426 120 $white 0 $line 0.8 | Out-Null
    Add-Text $slide 514 182 360 26 'PROMETHEE II' 17 $ink $true 1 | Out-Null
    Add-Text $slide 514 218 360 42 'Ranking completo por fluxos de preferência.' 13.5 $muted $false 1 | Out-Null
    Add-Rect $slide 491 294 426 120 $white 0 $line 0.8 | Out-Null
    Add-Text $slide 514 316 360 26 'ELECTRE III' 17 $ink $true 1 | Out-Null
    Add-Text $slide 514 352 360 45 'Sobreclassificação com limiares, veto e incomparabilidade.' 13.5 $muted $false 1 | Out-Null
    Add-Rect $slide 43 436 874 58 $charcoal | Out-Null
    Add-Text $slide 62 451 842 18 'CENÁRIO-BASE' 10.5 $gold $true 1 | Out-Null
    Add-Text $slide 62 471 842 17 'pesos iguais · q = 5% · p = 20% · veto = 60%' 12.5 $white $false 1 | Out-Null
    Add-Footer $slide 5
    Add-Note $slide "Tempo: 65 segundos.`nExplicar o quarto critério: mede o afastamento das receitas das pilhas em relação à receita média de cada equipamento. Justificar os métodos: PROMETHEE fornece ranking completo e ELECTRE preserva incomparabilidade. Pesos iguais refletem ausência de preferência externa confirmada."

    # 6. Recommendation
    $slide = $pres.Slides.Add(6, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Os dois métodos recomendam A073' 'Resultado principal' | Out-Null
    $selectedImage = Join-Path $root 'results\decision_final\selected_f1_f2.png'
    Add-Rect $slide 43 136 490 326 $white 0 $line 0.8 | Out-Null
    Add-PictureFit $slide $selectedImage 53 146 470 306 | Out-Null
    Add-Text $slide 565 142 100 22 'A073' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 565 172 145 30 'R$ 63,74 mi' 22 $oxide $true 1 | Out-Null
    Add-Text $slide 715 172 80 30 '3,3973' 21 $ink $true 1 | Out-Null
    Add-Text $slide 825 172 90 30 '2,6966' 21 $ink $true 1 | Out-Null
    Add-Text $slide 565 207 145 18 'custo' 11 $muted $false 1 | Out-Null
    Add-Text $slide 715 207 80 18 'f2' 11 $muted $false 1 | Out-Null
    Add-Text $slide 825 207 90 18 'f3' 11 $muted $false 1 | Out-Null
    Add-Text $slide 565 254 330 44 '• 1º lugar no PROMETHEE II.' 14.5 $ink $false 1 | Out-Null
    Add-Text $slide 565 304 330 50 '• Pertence ao conjunto máximo do ELECTRE III.' 14.5 $ink $false 1 | Out-Null
    Add-Text $slide 565 366 330 50 '• H = 0,042526: receita mais homogênea que alternativas químicas próximas.' 14.5 $ink $false 1 | Out-Null
    Add-Rect $slide 565 432 352 30 $peach | Out-Null
    Add-Text $slide 579 439 326 18 'A escolha equilibra custo, química e operação.' 11.5 $oxide $true 1 | Out-Null
    Add-Footer $slide 6
    Add-Note $slide "Tempo: 70 segundos.`nDestacar que A073 pertence ao conjunto máximo ELECTRE e lidera o PROMETHEE. O ELECTRE encontrou nove alternativas máximas; a regra adicional escolheu A073. Comparar: A045 custa menos e tem sílica semelhante, mas pior alumina. A072 tem química próxima, porém receita menos homogênea."

    # 7. Sensitivity
    $slide = $pres.Slides.Add(7, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'A073 vence na maioria dos cenários' 'Análise de sensibilidade' | Out-Null
    Add-Rect $slide 43 138 500 326 $white 0 $line 0.8 | Out-Null
    Add-Text $slide 65 158 450 22 'VITÓRIAS EM 15 CENÁRIOS' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 65 202 128 22 'PROMETHEE II' 13.5 $ink $true 1 | Out-Null
    Add-Text $slide 65 246 55 20 'A073' 12 $ink $true 1 | Out-Null
    Add-Rect $slide 132 244 312 24 $oxide | Out-Null
    Add-Text $slide 458 243 42 24 '12' 14 $oxide $true 1 | Out-Null
    Add-Text $slide 65 282 55 20 'A020' 12 $ink $true 1 | Out-Null
    Add-Rect $slide 132 280 78 24 $gold | Out-Null
    Add-Text $slide 224 279 42 24 '3' 14 $gold $true 1 | Out-Null
    Add-Text $slide 65 334 128 22 'ELECTRE III' 13.5 $ink $true 1 | Out-Null
    Add-Text $slide 65 378 55 20 'A073' 12 $ink $true 1 | Out-Null
    Add-Rect $slide 132 376 260 24 $oxide | Out-Null
    Add-Text $slide 406 375 42 24 '10' 14 $oxide $true 1 | Out-Null
    Add-Text $slide 65 414 55 20 'Outras' 12 $ink $true 1 | Out-Null
    Add-Rect $slide 132 412 130 24 $markerGray | Out-Null
    Add-Text $slide 276 411 42 24 '5' 14 $muted $true 1 | Out-Null
    Add-Text $slide 580 152 310 25 'O QUE MUDA A DECISÃO' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 580 198 305 54 'Peso de custo = 40%' 22 $ink $true 1 | Out-Null
    Add-Text $slide 580 258 160 34 'A020' 25 $oxide $true 1 | Out-Null
    Add-Text $slide 580 302 300 40 'R$ 60,62 mi, com desempenho químico inferior.' 14.5 $muted $false 1 | Out-Null
    Add-Rect $slide 580 368 314 76 $soft | Out-Null
    Add-Text $slide 598 386 278 44 'A073 é robusta, mas a preferência explícita por custo altera a recomendação.' 13.5 $ink $true 1 | Out-Null
    Add-Footer $slide 7
    Add-Note $slide "Tempo: 55 segundos.`nExplicar os 15 cenários: cinco perfis de peso e três escalas de limiar. A073 vence 12 vezes no PROMETHEE e 10 no ELECTRE. A mudança consistente ocorre quando o custo recebe peso 40%, levando a A020. Conclusão: robustez majoritária, mas não invariância a preferências."

    # 8. Final solution
    $slide = $pres.Slides.Add(8, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Composição e qualidade da solução final' 'A073 · solução recomendada' | Out-Null
    $finalImage = Join-Path $root 'results\decision_final\final_solution.png'
    Add-Rect $slide 43 132 440 356 $white 0 $line 0.8 | Out-Null
    Add-PictureFit $slide $finalImage 53 140 420 340 | Out-Null
    Add-Text $slide 515 148 145 30 'R$ 63,74 mi' 21 $oxide $true 1 | Out-Null
    Add-Text $slide 675 148 80 30 '3,3973' 20 $ink $true 1 | Out-Null
    Add-Text $slide 795 148 90 30 '2,6966' 20 $ink $true 1 | Out-Null
    Add-Text $slide 515 183 145 18 'custo' 11 $muted $false 1 | Out-Null
    Add-Text $slide 675 183 80 18 'f2' 11 $muted $false 1 | Out-Null
    Add-Text $slide 795 183 90 18 'f3' 11 $muted $false 1 | Out-Null
    Add-Text $slide 515 232 370 46 '• Dez pilhas, 145 caminhões e 290 kt.' 14.5 $ink $false 1 | Out-Null
    Add-Text $slide 515 292 370 48 '• Todas as restrições de massa, elegibilidade e qualidade são atendidas.' 14.5 $ink $false 1 | Out-Null
    Add-Text $slide 515 360 370 44 '• H = 0,042526 mede a homogeneidade operacional das receitas.' 14.5 $ink $false 1 | Out-Null
    Add-Rect $slide 515 430 390 34 $peach | Out-Null
    Add-Text $slide 530 438 360 18 'FACTÍVEL EM TODAS AS RESTRIÇÕES' 10.5 $oxide $true 1 | Out-Null
    Add-Footer $slide 8
    Add-Note $slide "Tempo: 60 segundos.`nMostrar a composição empilhada e os perfis químicos. As dez pilhas respeitam as faixas verdes. Destacar que o quarto critério observa a semelhança das proporções de minérios dentro de cada equipamento, além da qualidade final."

    # 9. Demo and conclusion
    $slide = $pres.Slides.Add(9, 12)
    $slide.Background.Fill.ForeColor.RGB = $paper
    $slide.Background.Fill.Solid()
    Add-Header $slide 'Demonstração e recomendação' 'Aplicação Streamlit' | Out-Null
    Add-Text $slide 43 136 390 22 'ROTEIRO DE 2 MINUTOS' 11 $oxide $true 1 | Out-Null
    $demo = @(
        @('1','Alternativas','Localizar A073 nas projeções.'),
        @('2','Comparação','Contrastar A073, A020 e A045.'),
        @('3','Métodos','Mostrar ranking e máximas ELECTRE.'),
        @('4','Solução final','Confirmar composição e factibilidade.')
    )
    for ($i = 0; $i -lt 4; $i++) {
        $y = 174 + $i * 58
        Add-Rect $slide 43 $y 30 30 $oxide | Out-Null
        Add-Text $slide 43 ($y + 3) 30 22 $demo[$i][0] 14 $white $true 2 | Out-Null
        Add-Text $slide 88 ($y - 1) 140 22 $demo[$i][1] 14.5 $ink $true 1 | Out-Null
        Add-Text $slide 230 ($y - 1) 245 36 $demo[$i][2] 12.5 $muted $false 1 | Out-Null
    }
    Add-Rect $slide 520 150 397 236 $white 0 $line 0.8 | Out-Null
    Add-Text $slide 546 174 340 22 'RECOMENDAÇÃO FINAL' 11 $oxide $true 1 | Out-Null
    Add-Text $slide 546 214 330 54 'Implementar A073 no cenário-base' 24 $ink $true 1 | Out-Null
    Add-Text $slide 546 286 330 70 'Equilibra custo, qualidade química e homogeneidade operacional. Com prioridade forte em custo, A020 deve ser reavaliada.' 14.5 $muted $false 1 | Out-Null
    Add-Rect $slide 43 426 874 58 $charcoal | Out-Null
    Add-Text $slide 62 441 840 18 'CONCLUSÃO' 10.5 $gold $true 1 | Out-Null
    Add-Text $slide 62 461 840 18 'A decisão permanece rastreável, reproduzível e sensível às preferências do decisor.' 12.5 $white $false 1 | Out-Null
    Add-Footer $slide 9
    Add-Note $slide "Tempo: 2 minutos, incluindo demonstração.`nAbrir o Streamlit já iniciado. Em Alternativas, mostrar f1 x f2 e os marcadores coincidentes. Em Comparar, selecionar A073, A020 e A045. Em Métodos, mostrar as nove máximas ELECTRE. Em Solução final, confirmar factibilidade e composição. Encerrar recomendando A073 no cenário-base e lembrando que A020 é a alternativa quando custo recebe prioridade forte."

    if (Test-Path -LiteralPath $pptxPath) {
        [System.IO.File]::Delete($pptxPath)
    }
    $pres.SaveAs($pptxPath, 24)
    $pres.Export($previewDir, 'PNG', 1280, 720)
}
finally {
    $pres.Close()
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

Write-Output $pptxPath
