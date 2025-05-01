$(document).ready(function() {
    // Initialize elements
    const $uploadArea = $('#uploadArea');
    const $previewSection = $('#previewSection');
    const $loader = $('#loader');
    const $resultSection = $('#resultSection');
    const $imageUpload = $('#imageUpload');
    const $imagePreview = $('#imagePreview');
    const $btnPredict = $('#btn-predict');
    const $tryAgainBtn = $('#tryAgainBtn');
    const $predictionResult = $('#predictionResult');
    const $confidenceBar = $('#confidenceBar');
    const $confidenceText = $('#confidenceText');
    const $resultImage = $('#resultImage');
    const $healthStars = $('#healthStars');
    const $healthTips = $('#healthTips');
    const $nutritionFacts = $('#nutritionFacts');
    const $mealHistory = $('#mealHistory');
    const $profileModal = $('#profileModal');

    // Initialize Bootstrap tooltips and popovers
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-bs-toggle="popover"]').popover({
        trigger: 'hover',
        html: true
    });

    // Load initial data
    updateDailyProgress();
    loadProfile();
    loadMealHistory();

    // Handle drag and drop
    $uploadArea.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('drag-over');
    });

    $uploadArea.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');
    });

    $uploadArea.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });

    // Handle file selection via button
    $imageUpload.on('change', function() {
        if (this.files && this.files[0]) {
            handleFiles(this.files);
        }
    });

    // Handle try again button
    $tryAgainBtn.on('click', resetUploader);

    // Handle predict button
    $btnPredict.on('click', predictFood);

    // Profile form submission
    $('#profileForm').on('submit', function(e) {
        e.preventDefault();
        saveProfile();
    });

    // Show profile modal when profile link is clicked
    $('.profile-link').on('click', function(e) {
        e.preventDefault();
        $profileModal.modal('show');
    });

    // Function to handle selected files
    function handleFiles(files) {
        const file = files[0];
        
        // Check file type
        const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showAlert('danger', 'Please upload a valid image file (JPEG, PNG, or WEBP)');
            return;
        }
        
        // Check file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            showAlert('danger', 'File size exceeds 5MB limit');
            return;
        }
        
        // Preview image
        const reader = new FileReader();
        reader.onload = function(e) {
            $imagePreview.attr('src', e.target.result);
            $uploadArea.hide();
            $previewSection.fadeIn(300);
        };
        reader.readAsDataURL(file);
    }

    function predictFood() {
        const file = $imageUpload[0].files[0];
        if (!file) {
            showAlert('danger', 'Please select an image first');
            return;
        }
        
        $previewSection.hide();
        $loader.fadeIn(300);
        $btnPredict.prop('disabled', true);
        
        const formData = new FormData();
        formData.append('file', file);
        
        $.ajax({
            type: 'POST',
            url: '/predict',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if (response.status === 'success') {
                    showResult(response);
                    updateDailyProgress();
                    loadMealHistory();
                } else {
                    showAlert('danger', response.error || 'Food recognition failed');
                    resetUploader();
                }
            },
            error: function(xhr) {
                let errorMsg = 'An error occurred during prediction';
                try {
                    const response = xhr.responseJSON || JSON.parse(xhr.responseText);
                    errorMsg = response.error || errorMsg;
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
                showAlert('danger', errorMsg);
                resetUploader();
            },
            complete: function() {
                $loader.hide();
                $btnPredict.prop('disabled', false);
            }
        });
    }

    function showResult(data) {
        console.log("API Response:", data); // Debug log
        
        // Ensure we have a valid confidence value
        let confidenceValue = 0;
        if (typeof data.confidence === 'number') {
            confidenceValue = data.confidence;
        } else if (typeof data.confidence === 'string') {
            confidenceValue = parseFloat(data.confidence.replace('%', ''));
        } else if (data.confidence_percent) {
            confidenceValue = parseFloat(data.confidence_percent.replace('%', ''));
        }
        
        console.log("Final Confidence Value:", confidenceValue); // Debug
    
        // Update confidence display
        $('#confidenceText').text(`Confidence: ${confidenceValue.toFixed(1)}%`);
        
        // Animate progress bar
        $('#confidenceBar').css('width', '0').animate({
            width: `${Math.min(100, confidenceValue)}%`
        }, 1000);
        const foodImg = $('#resultImage');
    foodImg.attr('src', data.image_url)
           .on('error', function() {
               // Fallback if image fails to load
               $(this).attr('src', 'static/images/food-placeholder.png');
               console.warn("Failed to load food image, using placeholder");
           });
           $('#foodEmoji').text(data.prediction.emoji || '🍽️');
           $('#foodName').text(data.prediction.name);
        // Display nutrition facts
        const nutritionHTML = `
            <div class="row g-3">
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-calories">
                            <i class="fas fa-fire"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.calories}</div>
                        <div class="nutrition-label">Calories</div>
                        <div class="nutrition-unit">kcal</div>
                    </div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-protein">
                            <i class="fas fa-dumbbell"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.protein}</div>
                        <div class="nutrition-label">Protein</div>
                        <div class="nutrition-unit">g</div>
                    </div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-carbs">
                            <i class="fas fa-bread-slice"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.carbs}</div>
                        <div class="nutrition-label">Carbs</div>
                        <div class="nutrition-unit">g</div>
                    </div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-fat">
                            <i class="fas fa-bacon"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.fat}</div>
                        <div class="nutrition-label">Fat</div>
                        <div class="nutrition-unit">g</div>
                    </div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-sodium">
                            <i class="fas fa-mortar-pestle"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.sodium}</div>
                        <div class="nutrition-label">Sodium</div>
                        <div class="nutrition-unit">mg</div>
                    </div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="nutrition-card">
                        <div class="nutrition-icon bg-fiber">
                            <i class="fas fa-seedling"></i>
                        </div>
                        <div class="nutrition-value">${data.prediction.fiber}</div>
                        <div class="nutrition-label">Fiber</div>
                        <div class="nutrition-unit">g</div>
                    </div>
                </div>
            </div>
        `;
        $nutritionFacts.html(nutritionHTML);
        
        // Display health rating stars
        $healthStars.empty();
        const rating = data.prediction.rating || 3;
        for (let i = 1; i <= 5; i++) {
            const starClass = i <= rating ? 'fas fa-star text-warning' : 'far fa-star text-secondary';
            $healthStars.append(`<i class="${starClass} me-1"></i>`);
        }
        
        // Display health tips
        $healthTips.empty();
        if (data.prediction.health_tips && data.prediction.health_tips.length > 0) {
            data.prediction.health_tips.forEach(tip => {
                const icon = tip.includes('⚠️') ? 'exclamation-triangle' : 
                            tip.includes('❌') ? 'times-circle' : 
                            tip.includes('🔹') ? 'info-circle' : 'lightbulb';
                $healthTips.append(`
                    <li class="list-group-item d-flex align-items-start">
                        <i class="fas fa-${icon} mt-1 me-2 text-${icon === 'exclamation-triangle' ? 'danger' : 
                          icon === 'times-circle' ? 'danger' : 
                          icon === 'info-circle' ? 'primary' : 'success'}"></i>
                        <span>${tip.replace(/⚠️|❌|🔹/g, '')}</span>
                    </li>
                `);
            });
        } else {
            $healthTips.append(`
                <li class="list-group-item text-muted">
                    No specific health tips available for this food.
                </li>
            `);
        }
        
        // Show impact cards
        const dailyLimits = {
            calories: 2000,
            sodium: 2300,
            protein: 50,
            carbs: 300,
            fat: 70
        };
        
        const impactHTML = `
            <div class="row g-3">
                <div class="col-md-6 col-lg-4">
                    <div class="impact-card ${data.prediction.calories > 500 ? 'high-impact' : ''}">
                        <div class="impact-icon bg-calories">
                            <i class="fas fa-fire"></i>
                        </div>
                        <div class="impact-content">
                            <h6>Calories</h6>
                            <h4>${data.prediction.calories} kcal</h4>
                            <div class="progress">
                                <div class="progress-bar bg-calories" 
                                    style="width: ${Math.min(100, (data.prediction.calories / dailyLimits.calories) * 100)}%">
                                    ${Math.round((data.prediction.calories / dailyLimits.calories) * 100)}%
                                </div>
                            </div>
                            <small>${Math.round((data.prediction.calories / dailyLimits.calories) * 100)}% of daily limit</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4">
                    <div class="impact-card ${data.prediction.sodium > 500 ? 'high-impact' : ''}">
                        <div class="impact-icon bg-sodium">
                            <i class="fas fa-mortar-pestle"></i>
                        </div>
                        <div class="impact-content">
                            <h6>Sodium</h6>
                            <h4>${data.prediction.sodium} mg</h4>
                            <div class="progress">
                                <div class="progress-bar bg-sodium" 
                                    style="width: ${Math.min(100, (data.prediction.sodium / dailyLimits.sodium) * 100)}%">
                                    ${Math.round((data.prediction.sodium / dailyLimits.sodium) * 100)}%
                                </div>
                            </div>
                            <small>${Math.round((data.prediction.sodium / dailyLimits.sodium) * 100)}% of daily limit</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-6 col-lg-4">
                    <div class="impact-card ${data.prediction.protein < 15 ? 'low-impact' : ''}">
                        <div class="impact-icon bg-protein">
                            <i class="fas fa-dumbbell"></i>
                        </div>
                        <div class="impact-content">
                            <h6>Protein</h6>
                            <h4>${data.prediction.protein} g</h4>
                            <div class="progress">
                                <div class="progress-bar bg-protein" 
                                    style="width: ${Math.min(100, (data.prediction.protein / dailyLimits.protein) * 100)}%">
                                    ${Math.round((data.prediction.protein / dailyLimits.protein) * 100)}%
                                </div>
                            </div>
                            <small>${Math.round((data.prediction.protein / dailyLimits.protein) * 100)}% of daily goal</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('#dailyImpact').html(impactHTML);
        $resultSection.addClass('fade-in').show();
        // At the end of showResult():
$resultSection.css('display', 'flex').hide().fadeIn(500);
    }

    function resetUploader() {
        $imageUpload.val('');
        $resultSection.hide().removeClass('fade-in');
        $previewSection.hide();
        $uploadArea.fadeIn(300);
        $confidenceBar.css('width', '0%');
    }

    function loadProfile() {
        $.get('/profile', function(data) {
            if (data.profile) {
                const profile = data.profile;
                $('[name="name"]').val(profile.name || '');
                $('[name="age"]').val(profile.age || '');
                $('[name="gender"]').val(profile.gender || 'other');
                $('[name="weight"]').val(profile.weight || '');
                $('[name="height"]').val(profile.height || '');
                $('[name="goal"]').val(profile.goal || 'maintain');
                $('[name="activity_level"]').val(profile.activity_level || 'moderate');
                $('[name="allergies"]').val(profile.allergies || '');
                $('[name="conditions"]').val(profile.conditions || '');
                $('[name="dietary_preferences"]').val(profile.dietary_preferences || '');
                
                // Update profile summary
                $('#profileSummary').html(`
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Name:</strong> ${profile.name || 'Not set'}</p>
                            <p><strong>Age:</strong> ${profile.age || 'Not set'}</p>
                            <p><strong>Gender:</strong> ${profile.gender || 'Not set'}</p>
                            <p><strong>Weight:</strong> ${profile.weight || 'Not set'} kg</p>
                            <p><strong>Height:</strong> ${profile.height || 'Not set'} cm</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Goal:</strong> ${formatGoal(profile.goal)}</p>
                            <p><strong>Activity Level:</strong> ${formatActivityLevel(profile.activity_level)}</p>
                            <p><strong>Allergies:</strong> ${profile.allergies || 'None'}</p>
                            <p><strong>Conditions:</strong> ${profile.conditions || 'None'}</p>
                            <p><strong>Dietary Preferences:</strong> ${profile.dietary_preferences || 'None'}</p>
                        </div>
                    </div>
                `);
            }
        }).fail(function() {
            console.log("Error loading profile data");
        });
    }
    
    function formatGoal(goal) {
        const goals = {
            'maintain': 'Maintain weight',
            'lose_weight': 'Lose weight',
            'gain_muscle': 'Gain muscle'
        };
        return goals[goal] || goal;
    }
    
    function formatActivityLevel(level) {
        const levels = {
            'sedentary': 'Sedentary',
            'light': 'Lightly active',
            'moderate': 'Moderately active',
            'active': 'Very active',
            'very_active': 'Extremely active'
        };
        return levels[level] || level;
    }
    
    function saveProfile() {
        const form = $('#profileForm');
        const formData = form.serialize();
        
        const submitBtn = form.find('button[type="submit"]');
        submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
        
        $.ajax({
            url: '/profile',
            type: 'POST',
            data: formData,
            success: function(response) {
                if (response.status === 'success') {
                    showAlert('success', 'Profile updated successfully!');
                    loadProfile();
                    updateDailyProgress(); // Refresh with new goals
                } else {
                    showAlert('danger', response.message || 'Profile update failed');
                }
            },
            error: function(xhr) {
                let errorMsg = 'Failed to save profile';
                try {
                    const response = xhr.responseJSON || JSON.parse(xhr.responseText);
                    errorMsg = response.message || errorMsg;
                    if (response.error) {
                        console.error('Server error:', response.error);
                    }
                } catch (e) {
                    console.error('Error parsing response:', e);
                }
                showAlert('danger', errorMsg);
            },
            complete: function() {
                submitBtn.prop('disabled', false).text('Save Profile');
            }
        });
    }

    function showAlert(type, message, duration=5000) {
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        // Create alert container if it doesn't exist
        if (!$('#alert-container').length) {
            $('body').append('<div id="alert-container" class="position-fixed top-0 end-0 p-3" style="z-index: 9999"></div>');
        }
        
        $('#alert-container').append(alertHtml);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            $('#' + alertId).alert('close');
        }, duration);
    }
    
    function updateDailyProgress() {
        $.get('/daily_intake', function(response) {
            if (response.status === 'success') {
                const { intake, limits, percentages, units } = response.data;
                
                // Update all progress bars
                updateProgressBar('#dailyProgress .progress-bar:eq(0)', 
                    percentages.calories, 
                    intake.calories, 
                    limits.calories, 
                    units.calories);
                    
                updateProgressBar('#dailyProgress .progress-bar:eq(1)', 
                    percentages.sodium, 
                    intake.sodium, 
                    limits.sodium, 
                    units.sodium);
                    
                updateProgressBar('#dailyProgress .progress-bar:eq(2)', 
                    percentages.protein, 
                    intake.protein, 
                    limits.protein, 
                    units.protein);
                    
                updateProgressBar('#dailyProgress .progress-bar:eq(3)', 
                    percentages.carbs, 
                    intake.carbs, 
                    limits.carbs, 
                    units.carbs);
                    
                updateProgressBar('#dailyProgress .progress-bar:eq(4)', 
                    percentages.fat, 
                    intake.fat, 
                    limits.fat, 
                    units.fat);
                
                // Update summary cards
                $('#dailySummary').html(`
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Today's Intake</h5>
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6 class="mb-1">Calories</h6>
                                            <h4>${Math.round(intake.calories)}/${Math.round(limits.calories)} ${units.calories}</h4>
                                        </div>
                                        <div class="text-end">
                                            <h6 class="mb-1">Remaining</h6>
                                            <h4>${Math.round(limits.calories - intake.calories)} ${units.calories}</h4>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <h5 class="card-title">Macronutrients</h5>
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6 class="mb-1">Protein</h6>
                                            <h4>${Math.round(intake.protein)}/${Math.round(limits.protein)} ${units.protein}</h4>
                                        </div>
                                        <div>
                                            <h6 class="mb-1">Carbs</h6>
                                            <h4>${Math.round(intake.carbs)}/${Math.round(limits.carbs)} ${units.carbs}</h4>
                                        </div>
                                        <div class="text-end">
                                            <h6 class="mb-1">Fat</h6>
                                            <h4>${Math.round(intake.fat)}/${Math.round(limits.fat)} ${units.fat}</h4>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `);
            }
        }).fail(function() {
            console.error("Failed to load daily intake data");
        });
    }
    
    function updateProgressBar(selector, percent, consumed, limit, unit) {
        const $bar = $(selector);
        const width = Math.min(100, percent);
        
        $bar.css('width', width + '%')
            .text(`${Math.round(consumed)}/${Math.round(limit)} ${unit}`)
            .removeClass('bg-success bg-warning bg-danger');
        
        // Color coding
        if (percent > 90) $bar.addClass('bg-danger');
        else if (percent > 70) $bar.addClass('bg-warning');
        else $bar.addClass('bg-success');
    }
    
    function loadMealHistory() {
        $.get('/meal_history', function(response) {
            if (response.status === 'success' && response.meals.length > 0) {
                let historyHTML = '';
                response.meals.forEach(meal => {
                    const date = new Date(meal.timestamp);
                    const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    
                    historyHTML += `
                        <div class="meal-history-item">
                            <div class="meal-time">${timeString}</div>
                            <div class="meal-image">
                                <img src="${meal.image_url || 'static/images/food-placeholder.png'}" alt="${meal.food_name}">
                            </div>
                            <div class="meal-details">
                                <h6>${meal.food_name}</h6>
                                <div class="meal-nutrition">
                                    <span class="badge bg-calories">${meal.calories} kcal</span>
                                    <span class="badge bg-protein">${meal.protein}g protein</span>
                                    <span class="badge bg-carbs">${meal.carbs}g carbs</span>
                                </div>
                            </div>
                        </div>
                    `;
                });
                $mealHistory.html(historyHTML);
            } else {
                $mealHistory.html('<div class="text-muted text-center py-4">No meals recorded today</div>');
            }
        }).fail(function() {
            $mealHistory.html('<div class="text-danger text-center py-4">Failed to load meal history</div>');
        });
    }
});
// $(document).ready(function() {
//     // Initialize elements
//     const $uploadArea = $('#uploadArea');
//     const $previewSection = $('#previewSection');
//     const $loader = $('#loader');
//     const $resultSection = $('#resultSection');
//     const $imageUpload = $('#imageUpload');
//     const $imagePreview = $('#imagePreview');
//     const $btnPredict = $('#btn-predict');
//     const $tryAgainBtn = $('#tryAgainBtn');
//     const $predictionResult = $('#predictionResult');
//     const $confidenceBar = $('#confidenceBar');
//     const $confidenceText = $('#confidenceText');
//     const $resultImage = $('#resultImage');
//     const $healthStars = $('#healthStars');
//     const $healthTips = $('#healthTips');
//     initBootstrap();
    
//     // Profile form submission
//     $('#profileForm').on('submit', function(e) {
//         e.preventDefault();
//         saveProfile();
//     });
//     // Load initial data
//     loadProfile();
//     updateDailyProgress();

//     // Handle drag and drop
//     $uploadArea.on('dragover', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).addClass('drag-over');
//     });

//     $uploadArea.on('dragleave', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).removeClass('drag-over');
//     });

//     $uploadArea.on('drop', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).removeClass('drag-over');
        
//         const files = e.originalEvent.dataTransfer.files;
//         if (files.length > 0) {
//             handleFiles(files);
//         }
//     });

//     // Handle file selection via button
//     $imageUpload.on('change', function() {
//         if (this.files && this.files[0]) {
//             handleFiles(this.files);
//         }
//     });

//     // Handle try again button
//     $tryAgainBtn.on('click', function() {
//         resetUploader();
//     });

//     // Handle predict button
//     $btnPredict.on('click', function() {
//         predictFood();
//     });

//     // Profile form submission
//     $('#profileForm').on('submit', function(e) {
//         e.preventDefault();
//         saveProfile();
//     });

//     // Function to handle selected files
//     function handleFiles(files) {
//         const file = files[0];
        
//         // Check file type
//         const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
//         if (!validTypes.includes(file.type)) {
//             showError('Please upload a valid image file (JPEG, PNG, or WEBP)');
//             return;
//         }
        
//         // Check file size (5MB max)
//         if (file.size > 5 * 1024 * 1024) {
//             showError('File size exceeds 5MB limit');
//             return;
//         }
        
//         // Preview image
//         const reader = new FileReader();
//         reader.onload = function(e) {
//             $imagePreview.attr('src', e.target.result);
//             $uploadArea.hide();
//             $previewSection.fadeIn(300);
//         };
//         reader.readAsDataURL(file);
//     }

//     // Function to predict food
//     // function predictFood() {
//     //     const file = $imageUpload[0].files[0];
//     //     if (!file) {
//     //         showError('Please select an image first');
//     //         return;
//     //     }
        
//     //     $previewSection.hide();
//     //     $loader.fadeIn(300);
        
//     //     const formData = new FormData();
//     //     formData.append('file', file);
        
//     //     $.ajax({
//     //         type: 'POST',
//     //         url: '/predict',
//     //         data: formData,
//     //         contentType: false,
//     //         processData: false,
//     //         success: function(response) {
//     //             if (response.error) {
//     //                 showError(response.error);
//     //             } else {
//     //                 showResult(response);
//     //                 updateDailyProgress();
//     //             }
//     //         },
//     //         error: function(xhr) {
//     //             let errorMsg = 'An error occurred';
//     //             if (xhr.responseJSON && xhr.responseJSON.error) {
//     //                 errorMsg = xhr.responseJSON.error;
//     //             } else if (xhr.status === 413) {
//     //                 errorMsg = 'File size too large';
//     //             } else if (xhr.status === 415) {
//     //                 errorMsg = 'Unsupported file type';
//     //             }
//     //             showError(errorMsg);
//     //         },
//     //         complete: function() {
//     //             $loader.hide();
//     //         }
//     //     });
//     // }
//     function predictFood() {
//         const file = $('#imageUpload')[0].files[0];
//         if (!file) {
//             showAlert('danger', 'Please select an image first');
//             return;
//         }
        
//         // Show loading state
//         $previewSection.hide();
//         $loader.fadeIn(300);
//         $btnPredict.prop('disabled', true);
        
//         const formData = new FormData();
//         formData.append('file', file);
        
//         $.ajax({
//             url: '/predict',
//             type: 'POST',
//             data: formData,
//             contentType: false,
//             processData: false,
//             success: function(response) {
//                 if (response.status === 'success') {
//                     showResult(response);
//                     updateDailyProgress();
//                 } else {
//                     showAlert('danger', response.error || 'Food recognition failed');
//                     resetUploader();
//                 }
//             },
//             error: function(xhr) {
//                 let errorMsg = 'An error occurred during prediction';
//                 try {
//                     const response = xhr.responseJSON || JSON.parse(xhr.responseText);
//                     errorMsg = response.error || errorMsg;
//                 } catch (e) {
//                     console.error('Error parsing response:', e);
//                 }
//                 showAlert('danger', errorMsg);
//                 resetUploader();
//             },
//             complete: function() {
//                 $loader.hide();
//                 $btnPredict.prop('disabled', false);
//             }
//         });
//     }

//     // Function to show prediction result
//     function showResult(data) {
//         $resultImage.attr('src', data.image_url);
//         $predictionResult.text(data.prediction.name);
        
//         // Display nutrition facts
//         $('#calories').text(data.prediction.calories + ' kcal');
//         $('#protein').text(data.prediction.protein + 'g');
//         $('#carbs').text(data.prediction.carbs + 'g');
//         $('#fat').text(data.prediction.fat + 'g');
//         $('#fiber').text(data.prediction.fiber + 'g');
//         $('#sodium').text(data.prediction.sodium + 'mg');
        
//         // Display health rating stars
//         $healthStars.empty();
//         const rating = data.prediction.rating || 3;
//         for (let i = 1; i <= 5; i++) {
//             const starClass = i <= rating ? 'fas fa-star text-warning' : 'far fa-star text-secondary';
//             $healthStars.append(`<i class="${starClass} me-1"></i>`);
//         }
        
//         // Display health tips
//         $healthTips.empty();
//         data.prediction.health_tips.forEach(tip => {
//             $healthTips.append(`<li class="list-group-item"><i class="fas fa-lightbulb text-primary me-2"></i>${tip}</li>`);
//         });
        
//         // Animate confidence bar
//         const confidencePercent = data.confidence.replace('%', '');
//         $confidenceBar.css('width', '0%').animate({
//             width: confidencePercent + '%'
//         }, 1000, function() {
//             $confidenceText.text('Analysis Confidence: ' + data.confidence);
//         });
        
//         $resultSection.addClass('fade-in').show();
//     }

//     // Function to show error
//     function showError(message) {
//         $loader.hide();
        
//         // Remove any existing alerts first
//         $('.alert-danger').alert('dispose').remove();
        
//         // Create new alert
//         const $errorAlert = $(`
//             <div class="alert alert-danger alert-dismissible fade show" role="alert">
//                 <strong>Error!</strong> <span class="error-message">${message}</span>
//                 <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
//             </div>
//         `).insertBefore($uploadArea);
        
//         // Initialize Bootstrap alert
//         new bootstrap.Alert($errorAlert[0]);
        
//         // Reset uploader after showing error
//         setTimeout(resetUploader, 3000);
//     }

//     // Function to reset uploader
//     function resetUploader() {
//         $imageUpload.val('');
//         $resultSection.hide().removeClass('fade-in');
//         $previewSection.hide();
//         $uploadArea.fadeIn(300);
//         $confidenceBar.css('width', '0%');
//         $('.alert-danger').alert('close');
//     }

//     // Load user profile
//     function loadProfile() {
//         $.get('/profile', function(data) {
//             if (data.goal) $('[name="goal"]').val(data.goal);
//             if (data.allergies) $('[name="allergies"]').val(data.allergies);
//             if (data.conditions) $('[name="conditions"]').val(data.conditions);
//         }).fail(function() {
//             console.log("Using default profile values");
//         });
//     }
    
//     // Save profile
//     // Initialize Bootstrap alerts properly
// function initBootstrap() {
//     // Initialize tooltips
//     $('[data-bs-toggle="tooltip"]').tooltip();
    
//     // Initialize alerts
//     $('.alert').alert();
// }

// // Safe profile saving
// // function saveProfile() {
// //     const formData = $('#profileForm').serialize();
    
// //     $.ajax({
// //         url: '/profile',
// //         type: 'POST',
// //         data: formData,
// //         success: function(response) {
// //             if (response.status === 'success') {
// //                 showAlert('success', response.message || 'Profile saved successfully!');
// //             } else {
// //                 showAlert('danger', response.message || 'Failed to save profile');
// //             }
// //         },
// //         error: function(xhr) {
// //             let errorMsg = 'Failed to save profile';
// //             try {
// //                 const response = JSON.parse(xhr.responseText);
// //                 errorMsg = response.message || errorMsg;
// //             } catch (e) {
// //                 console.error('Error parsing response:', e);
// //             }
// //             showAlert('danger', errorMsg);
// //         }
// //     });
// // }
// function saveProfile() {
//     const form = $('#profileForm');
//     const formData = form.serialize();
    
//     // Show loading state
//     const submitBtn = form.find('button[type="submit"]');
//     submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
    
//     $.ajax({
//         url: '/profile',
//         type: 'POST',
//         data: formData,
//         success: function(response) {
//             if (response.status === 'success') {
//                 showAlert('success', 'Profile updated successfully!');
//             } else {
//                 showAlert('danger', response.message || 'Profile update failed');
//             }
//         },
//         error: function(xhr) {
//             let errorMsg = 'Failed to save profile';
//             try {
//                 const response = JSON.parse(xhr.responseText);
//                 errorMsg = response.message || errorMsg;
//             } catch (e) {
//                 console.error('Error parsing response:', e);
//             }
//             showAlert('danger', errorMsg);
//         },
//         complete: function() {
//             submitBtn.prop('disabled', false).text('Save Profile');
//         }
//     });
// }


// function showAlert(type, message, duration=5000) {
//     // Create alert container if it doesn't exist
//     if (!$('#alert-container').length) {
//         $('main.container').prepend('<div id="alert-container"></div>');
//     }
    
//     // Create alert HTML
//     const alertId = 'alert-' + Date.now();
//     const alertHtml = `
//         <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
//             ${message}
//             <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//         </div>
//     `;
    
//     // Add to container
//     $('#alert-container').append(alertHtml);
    
//     // Initialize the alert
//     const alertElement = document.getElementById(alertId);
//     const alert = new bootstrap.Alert(alertElement);
    
//     // Auto-dismiss after duration
//     setTimeout(() => {
//         alert.close();
//     }, duration);
    
//     // Clean up after dismissal
//     alertElement.addEventListener('closed.bs.alert', () => {
//         $(alertElement).remove();
//     });
// }
    
//     // Update daily progress bars
//     function updateDailyProgress() {
//         $.get('/daily_intake', function(data) {
//             if (!data.error) {
//                 const consumed = data.consumed;
//                 const limits = data.limits;
//                 const percentages = data.percentages;
                
//                 // Update progress bars
//                 updateProgressBar('#dailyProgress .progress-bar:eq(0)', 
//                     percentages.calories, consumed.calories, limits.calories, 'kcal');
//                 updateProgressBar('#dailyProgress .progress-bar:eq(1)', 
//                     percentages.sodium, consumed.sodium, limits.sodium, 'mg');
//                 updateProgressBar('#dailyProgress .progress-bar:eq(2)', 
//                     percentages.protein, consumed.protein, limits.protein, 'g');
//                 updateProgressBar('#dailyProgress .progress-bar:eq(3)', 
//                     percentages.carbs, consumed.carbs, limits.carbs, 'g');
//             }
//         }).fail(function() {
//             console.log("Daily intake not available");
//         });
//     }
    
//     function updateProgressBar(selector, percent, consumed, limit, unit) {
//         const $bar = $(selector);
//         const width = Math.min(100, percent);
//         $bar.css('width', width + '%');
//         $bar.text(`${Math.round(consumed)}/${limit} ${unit}`);
        
//         // Change color based on percentage
//         if (percent > 90) {
//             $bar.removeClass('bg-success bg-warning').addClass('bg-danger');
//         } else if (percent > 70) {
//             $bar.removeClass('bg-success bg-danger').addClass('bg-warning');
//         } else {
//             $bar.removeClass('bg-warning bg-danger').addClass('bg-success');
//         }
//     }
// });

// $(document).ready(function() {
//     // Initialize elements
//     const $uploadArea = $('#uploadArea');
//     const $previewSection = $('#previewSection');
//     const $loader = $('#loader');
//     const $resultSection = $('#resultSection');
//     const $imageUpload = $('#imageUpload');
//     const $imagePreview = $('#imagePreview');
//     const $btnPredict = $('#btn-predict');
//     const $tryAgainBtn = $('#tryAgainBtn');
//     const $predictionResult = $('#predictionResult');
//     const $confidenceBar = $('#confidenceBar');
//     const $confidenceText = $('#confidenceText');
//     const $resultImage = $('#resultImage');
//     const $healthStars = $('#healthStars');
//     const $healthTips = $('#healthTips');

//     // Initialize Bootstrap tooltips
//     $('[data-bs-toggle="tooltip"]').tooltip();
//     updateDailyProgress();
//     // Handle drag and drop
//     $uploadArea.on('dragover', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).addClass('drag-over');
//     });

//     $uploadArea.on('dragleave', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).removeClass('drag-over');
//     });

//     $uploadArea.on('drop', function(e) {
//         e.preventDefault();
//         e.stopPropagation();
//         $(this).removeClass('drag-over');
        
//         const files = e.originalEvent.dataTransfer.files;
//         if (files.length > 0) {
//             handleFiles(files);
//         }
//     });

//     // Handle file selection via button
//     $imageUpload.on('change', function() {
//         if (this.files && this.files[0]) {
//             handleFiles(this.files);
//         }
//     });

//     // Handle try again button
//     $tryAgainBtn.on('click', resetUploader);

//     // Handle predict button
//     $btnPredict.on('click', predictFood);

//     // Profile form submission
//     $('#profileForm').on('submit', function(e) {
//         e.preventDefault();
//         saveProfile();
//     });

//     // Load initial data
//     loadProfile();
//     updateDailyProgress();

//     // Function to handle selected files
//     function handleFiles(files) {
//         const file = files[0];
        
//         // Check file type
//         const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
//         if (!validTypes.includes(file.type)) {
//             showAlert('danger', 'Please upload a valid image file (JPEG, PNG, or WEBP)');
//             return;
//         }
        
//         // Check file size (5MB max)
//         if (file.size > 5 * 1024 * 1024) {
//             showAlert('danger', 'File size exceeds 5MB limit');
//             return;
//         }
        
//         // Preview image
//         const reader = new FileReader();
//         reader.onload = function(e) {
//             $imagePreview.attr('src', e.target.result);
//             $uploadArea.hide();
//             $previewSection.fadeIn(300);
//         };
//         reader.readAsDataURL(file);
//     }

//     function predictFood() {
//         const file = $imageUpload[0].files[0];
//         if (!file) {
//             showAlert('danger', 'Please select an image first');
//             return;
//         }
        
//         $previewSection.hide();
//         $loader.fadeIn(300);
//         $btnPredict.prop('disabled', true);
        
//         const formData = new FormData();
//         formData.append('file', file);
        
//         $.ajax({
//             type: 'POST',
//             url: '/predict',
//             data: formData,
//             contentType: false,
//             processData: false,
//             success: function(response) {
//                 if (response.status === 'success') {
//                     showResult(response);
//                     updateDailyProgress();
//                 } else {
//                     showAlert('danger', response.error || 'Food recognition failed');
//                     resetUploader();
//                 }
//             },
//             error: function(xhr) {
//                 let errorMsg = 'An error occurred during prediction';
//                 try {
//                     const response = xhr.responseJSON || JSON.parse(xhr.responseText);
//                     errorMsg = response.error || errorMsg;
//                 } catch (e) {
//                     console.error('Error parsing response:', e);
//                 }
//                 showAlert('danger', errorMsg);
//                 resetUploader();
//             },
//             complete: function() {
//                 $loader.hide();
//                 $btnPredict.prop('disabled', false);
//             }
//         });
//     }

//     function showResult(data) {
//         $resultImage.attr('src', data.image_url);
//         $predictionResult.text(data.prediction.name);
        
//         // Display nutrition facts
//         $('#calories').text(data.prediction.calories + ' kcal');
//         $('#protein').text(data.prediction.protein + 'g');
//         $('#carbs').text(data.prediction.carbs + 'g');
//         $('#fat').text(data.prediction.fat + 'g');
//         $('#fiber').text(data.prediction.fiber + 'g');
//         $('#sodium').text(data.prediction.sodium + 'mg');
        
//         // Display health rating stars
//         $healthStars.empty();
//         const rating = data.prediction.rating || 3;
//         for (let i = 1; i <= 5; i++) {
//             const starClass = i <= rating ? 'fas fa-star text-warning' : 'far fa-star text-secondary';
//             $healthStars.append(`<i class="${starClass} me-1"></i>`);
//         }
        
//         // Display health tips
//         $healthTips.empty();
//         data.prediction.health_tips.forEach(tip => {
//             $healthTips.append(`<li class="list-group-item"><i class="fas fa-lightbulb text-primary me-2"></i>${tip}</li>`);
//         });
        
//         // Animate confidence bar
//         const confidencePercent = data.confidence.replace('%', '');
//         $confidenceBar.css('width', '0%').animate({
//             width: confidencePercent + '%'
//         }, 1000, function() {
//             $confidenceText.text('Analysis Confidence: ' + data.confidence);
//         });
//         const impactHTML = `
//         <div class="col-md-4 mb-3">
//             <div class="impact-card p-3 rounded-3 ${data.prediction.calories > 500 ? 'bg-warning-light' : 'bg-info-light'}">
//                 <div class="d-flex align-items-center">
//                     <div class="impact-icon bg-primary text-white rounded-circle me-3">
//                         <i class="fas fa-fire"></i>
//                     </div>
//                     <div>
//                         <h6 class="mb-0">Calories</h6>
//                         <h4 class="mb-0">${data.prediction.calories} kcal</h4>
//                         <small>${Math.round((data.prediction.calories/2000)*100)}% of daily limit</small>
//                     </div>
//                 </div>
//             </div>
//         </div>
//         <div class="col-md-4 mb-3">
//             <div class="impact-card p-3 rounded-3 ${data.prediction.sodium > 500 ? 'bg-warning-light' : 'bg-info-light'}">
//                 <div class="d-flex align-items-center">
//                     <div class="impact-icon bg-danger text-white rounded-circle me-3">
//                         <i class="fas fa-mortar-pestle"></i>
//                     </div>
//                     <div>
//                         <h6 class="mb-0">Sodium</h6>
//                         <h4 class="mb-0">${data.prediction.sodium} mg</h4>
//                         <small>${Math.round((data.prediction.sodium/2300)*100)}% of daily limit</small>
//                     </div>
//                 </div>
//             </div>
//         </div>
//         <div class="col-md-4 mb-3">
//             <div class="impact-card p-3 rounded-3 ${data.prediction.protein < 15 ? 'bg-warning-light' : 'bg-info-light'}">
//                 <div class="d-flex align-items-center">
//                     <div class="impact-icon bg-success text-white rounded-circle me-3">
//                         <i class="fas fa-dumbbell"></i>
//                     </div>
//                     <div>
//                         <h6 class="mb-0">Protein</h6>
//                         <h4 class="mb-0">${data.prediction.protein} g</h4>
//                         <small>${Math.round((data.prediction.protein/50)*100)}% of daily goal</small>
//                     </div>
//                 </div>
//             </div>
//         </div>
//     `;
    
//     $('#dailyImpact').html(impactHTML);
//         $resultSection.addClass('fade-in').show();
//         updateDailyProgress();
//     }

//     function resetUploader() {
//         $imageUpload.val('');
//         $resultSection.hide().removeClass('fade-in');
//         $previewSection.hide();
//         $uploadArea.fadeIn(300);
//         $confidenceBar.css('width', '0%');
//     }

//     function loadProfile() {
//         $.get('/profile', function(data) {
//             if (data.goal) $('[name="goal"]').val(data.goal);
//             if (data.allergies) $('[name="allergies"]').val(data.allergies);
//             if (data.conditions) $('[name="conditions"]').val(data.conditions);
//         }).fail(function() {
//             console.log("Using default profile values");
//         });
//     }
    
//     function saveProfile() {
//         const form = $('#profileForm');
//         const formData = form.serialize();
        
//         const submitBtn = form.find('button[type="submit"]');
//         submitBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...');
        
//         $.ajax({
//             url: '/profile',
//             type: 'POST',
//             data: formData,
//             success: function(response) {
//                 if (response.status === 'success') {
//                     showAlert('success', response.message || 'Profile updated successfully!');
//                 } else {
//                     showAlert('danger', response.message || 'Profile update failed');
//                 }
//             },
//             error: function(xhr) {
//                 let errorMsg = 'Failed to save profile';
//                 try {
//                     const response = xhr.responseJSON || JSON.parse(xhr.responseText);
//                     errorMsg = response.message || errorMsg;
//                     if (response.error) {
//                         console.error('Server error:', response.error);
//                     }
//                 } catch (e) {
//                     console.error('Error parsing response:', e);
//                 }
//                 showAlert('danger', errorMsg);
//             },
//             complete: function() {
//                 submitBtn.prop('disabled', false).text('Save Profile');
//             }
//         });
//     }

//     function showAlert(type, message, duration=5000) {
//         const alertId = 'alert-' + Date.now();
//         const alertHtml = `
//             <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
//                 ${message}
//                 <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//             </div>
//         `;
        
//         // Create alert container if it doesn't exist
//         if (!$('#alert-container').length) {
//             $('body').append('<div id="alert-container" class="position-fixed top-0 end-0 p-3" style="z-index: 9999"></div>');
//         }
        
//         $('#alert-container').append(alertHtml);
        
//         // Auto-dismiss after duration
//         setTimeout(() => {
//             $('#' + alertId).alert('close');
//         }, duration);
//     }
    
//     function updateDailyProgress() {
//         $.get('/daily_intake', function(response) {
//             if (response.status === 'success') {
//                 const { consumed, limits, percentages } = response;
                
//                 // Update all progress bars
//                 updateProgressBar('#dailyProgress .progress-bar:eq(0)', 
//                     percentages.calories, 
//                     consumed.calories, 
//                     limits.calories, 
//                     'kcal');
                    
//                 updateProgressBar('#dailyProgress .progress-bar:eq(1)', 
//                     percentages.sodium, 
//                     consumed.sodium, 
//                     limits.sodium, 
//                     'mg');
                    
//                 updateProgressBar('#dailyProgress .progress-bar:eq(2)', 
//                     percentages.protein, 
//                     consumed.protein, 
//                     limits.protein, 
//                     'g');
                    
//                 updateProgressBar('#dailyProgress .progress-bar:eq(3)', 
//                     percentages.carbs, 
//                     consumed.carbs, 
//                     limits.carbs, 
//                     'g');
                    
//                 // Add fat display if you have a 5th progress bar
//                 updateProgressBar('#dailyProgress .progress-bar:eq(4)', 
//                     percentages.fat, 
//                     consumed.fat, 
//                     limits.fat, 
//                     'g');
//             }
//         }).fail(function() {
//             console.error("Failed to load daily intake data");
//         });
//     }
    
//     function updateProgressBar(selector, percent, consumed, limit, unit) {
//         const $bar = $(selector);
//         const width = Math.min(100, percent);
        
//         $bar.css('width', width + '%')
//             .text(`${Math.round(consumed)}/${limit} ${unit}`)
//             .removeClass('bg-success bg-warning bg-danger');
        
//         // Color coding
//         if (percent > 90) $bar.addClass('bg-danger');
//         else if (percent > 70) $bar.addClass('bg-warning');
//         else $bar.addClass('bg-success');
//     }
    
//     // Call this when page loads
//     $(document).ready(function() {
//         updateDailyProgress();
        
//         // Also call after each food prediction
//         function showResult(data) {
//             // ... existing result display code ...
//             updateDailyProgress();
//         }
//     });
// });